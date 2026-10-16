import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def run(command):
    return subprocess.check_output(command, text=True).strip()


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]))


def build():
    script = (ROOT / "demo/demo-script.md").read_text()
    sections = re.split(r"(?m)^### Slide \d+:", script)[1:]
    narration = [re.search(r'SAY: "(.*?)"', section, re.S).group(1) for section in sections]
    slides = json.loads((ROOT / "demo/slides.json").read_text())
    if len(narration) != len(slides):
        raise ValueError("Each slide needs one matching narration paragraph")
    segments = []
    timing = []
    with tempfile.TemporaryDirectory(prefix="resolvedesk-presentation-") as temporary:
        work = Path(temporary)
        for index, spoken in enumerate(narration, 1):
            prefix = work / f"slide-{index}"
            text = prefix.with_suffix(".txt")
            text.write_text(spoken)
            audio = prefix.with_suffix(".aiff")
            run(["say", "-v", "Samantha", "-r", "165", "-f", str(text), "-o", str(audio)])
            run(["pdftoppm", "-f", str(index), "-singlefile", "-scale-to", "1440", "-png", str(ROOT / "demo/slides.pdf"), str(prefix)])
            seconds = duration(audio) + 1.2
            video = prefix.with_suffix(".mp4")
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "25", "-i", str(prefix.with_suffix(".png")), "-i", str(audio), "-vf", "scale=1440:900:force_original_aspect_ratio=decrease,pad=1440:900:(ow-iw)/2:(oh-ih)/2:color=0x101f25", "-af", "apad", "-t", str(seconds), "-c:v", "libx264", "-preset", "fast", "-tune", "stillimage", "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "1", str(video)])
            segments.append(video)
            timing.append({"slide": index, "title": slides[index - 1]["title"], "seconds": duration(video), "narration": spoken})
        manifest = work / "segments.txt"
        manifest.write_text("".join(f"file '{segment}'\n" for segment in segments))
        output = ROOT / "demo/presentation.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", "-movflags", "+faststart", str(output)])
    metadata = {"voice": "macOS Samantha", "rate": 165, "seconds": duration(output), "slides": timing}
    (ROOT / "demo/presentation-video.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"output": str(output), "seconds": metadata["seconds"]}))


if __name__ == "__main__":
    build()
