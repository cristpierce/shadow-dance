"""Append a frozen affine action adapter to the public SONIC decoder ONNX."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnx import helper, numpy_helper


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    adapter = json.loads(args.adapter.read_text(encoding="utf-8"))
    gain = np.asarray(adapter["gain"], dtype=np.float32).reshape(1, 29)
    bias = np.asarray(adapter["bias"], dtype=np.float32).reshape(1, 29)
    if gain.shape != (1, 29) or bias.shape != (1, 29):
        raise ValueError("adapter must contain 29 gains and 29 biases")
    if not np.isfinite(gain).all() or not np.isfinite(bias).all():
        raise ValueError("adapter contains non-finite values")

    model = onnx.load(args.decoder)
    if len(model.graph.output) != 1 or model.graph.output[0].name != "action":
        raise ValueError("unexpected public decoder output contract")
    stock_output = "shadow_dance_stock_action"
    for node in model.graph.node:
        node.output[:] = [stock_output if name == "action" else name for name in node.output]
        node.input[:] = [stock_output if name == "action" else name for name in node.input]

    model.graph.initializer.extend(
        [
            numpy_helper.from_array(gain, name="shadow_dance_adapter_gain"),
            numpy_helper.from_array(bias, name="shadow_dance_adapter_bias"),
        ]
    )
    model.graph.node.extend(
        [
            helper.make_node(
                "Mul",
                [stock_output, "shadow_dance_adapter_gain"],
                ["shadow_dance_scaled_action"],
                name="ShadowDanceAffineGain",
            ),
            helper.make_node(
                "Add",
                ["shadow_dance_scaled_action", "shadow_dance_adapter_bias"],
                ["action"],
                name="ShadowDanceAffineBias",
            ),
        ]
    )
    model.doc_string = (
        "NVIDIA public GEAR-SONIC decoder with Team SELTZER's training-only bounded "
        "affine action calibration. Experimental MuJoCo deployment proxy; not an "
        "Isaac/PPO or WBT-Bench result."
    )
    metadata = {
        "shadow_dance_format": "affine_proxy_adapter_v1",
        "shadow_dance_adapter_sha256": sha256(args.adapter),
        "shadow_dance_parent_decoder_sha256": sha256(args.decoder),
        "shadow_dance_official_sonic_recipe": "false",
        "shadow_dance_official_wbt_bench": "false",
        "shadow_dance_isaac_result": "false",
        "license": "NVIDIA Open Model License",
        "attribution": "Licensed by NVIDIA Corporation under the NVIDIA Open Model License.",
    }
    del model.metadata_props[:]
    for key, value in metadata.items():
        item = model.metadata_props.add()
        item.key = key
        item.value = value

    onnx.checker.check_model(model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, args.output)

    stock = ort.InferenceSession(str(args.decoder), providers=["CPUExecutionProvider"])
    adapted = ort.InferenceSession(str(args.output), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(20260816)
    maxima = []
    finite = True
    for _ in range(5):
        observation = rng.normal(0.0, 0.25, (1, 994)).astype(np.float32)
        stock_action = stock.run(None, {"obs_dict": observation})[0]
        expected = stock_action * gain + bias
        actual = adapted.run(None, {"obs_dict": observation})[0]
        finite = finite and bool(np.isfinite(actual).all())
        maxima.append(float(np.max(np.abs(expected - actual))))
    if not finite or max(maxima) > 1e-6:
        raise ValueError("adapted ONNX failed finite/equivalence probe")

    report = {
        "format": "shadow_dance_affine_decoder_onnx_validation_v1",
        "official_sonic_recipe": False,
        "official_wbt_bench": False,
        "isaac_result": False,
        "parent_decoder": {
            "path": args.decoder.as_posix(),
            "sha256": sha256(args.decoder),
        },
        "adapter": {"path": args.adapter.as_posix(), "sha256": sha256(args.adapter)},
        "output": {
            "path": args.output.as_posix(),
            "sha256": sha256(args.output),
            "bytes": args.output.stat().st_size,
        },
        "onnx_checker_passed": True,
        "onnxruntime_cpu_probes": 5,
        "all_outputs_finite": finite,
        "max_affine_equivalence_error": max(maxima),
        "input_contract": {"obs_dict": [1, 994]},
        "output_contract": {"action": [1, 29]},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
