#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://api.openai.com/v1"


def build_multipart_body(fields: list[tuple[str, str]], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----codex-openai-{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    for name, path in files:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode(
                "utf-8"
            )
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body.extend(path.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), boundary


def post_json(endpoint: str, fields: list[tuple[str, str]], files: list[tuple[str, Path]]) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI image generation.")

    body, boundary = build_multipart_body(fields, files)
    request = Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        message = error.read().decode("utf-8", errors="replace") if error.fp else ""
        raise RuntimeError(f"OpenAI API request failed: {error.code} {error.reason}\n{message}") from error
    except URLError as error:
        raise RuntimeError(f"OpenAI API request failed: {error.reason}") from error

    return json.loads(payload)


def save_image_from_response(payload: dict, output_path: Path) -> None:
    data = payload.get("data") or []
    if not data:
        raise RuntimeError(f"OpenAI response did not include image data: {payload}")

    first = data[0]
    if "b64_json" in first:
        output_path.write_bytes(base64.b64decode(first["b64_json"]))
        return

    if "url" in first:
        raise RuntimeError(
            "OpenAI response returned a URL instead of base64 data. "
            "Update the adapter to handle URL downloads."
        )

    raise RuntimeError(f"OpenAI response missing image payload: {payload}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a candidate sheet with OpenAI image generation.")
    parser.add_argument("--prompt-file", required=True, help="Path to the prompt markdown/text file.")
    parser.add_argument("--output", required=True, help="Path to write the generated PNG.")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Reference image path. Repeat for multiple anchors.",
    )
    parser.add_argument("--model", default="gpt-image-2", help="Image generation model.")
    parser.add_argument("--size", default="auto", help="Requested output size.")
    parser.add_argument("--quality", default="high", help="Requested image quality.")
    parser.add_argument("--background", default="auto", help="Requested background mode.")
    args = parser.parse_args(argv)

    prompt_path = Path(args.prompt_file)
    output_path = Path(args.output)
    prompt = prompt_path.read_text(encoding="utf-8")
    images = [Path(path) for path in args.image]

    endpoint = f"{DEFAULT_API_BASE}/images/edits" if images else f"{DEFAULT_API_BASE}/images/generations"
    fields = [
        ("model", args.model),
        ("prompt", prompt),
        ("size", args.size),
        ("quality", args.quality),
        ("background", args.background),
    ]
    files = [("image[]", image_path) for image_path in images]

    payload = post_json(endpoint, fields, files)
    save_image_from_response(payload, output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
