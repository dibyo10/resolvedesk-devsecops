import argparse
import json
import html
from pathlib import Path
import subprocess
import tempfile
import time
from playwright.sync_api import sync_playwright


def run(command):
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def duration(path):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(path)]).strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='capstone-video-') as temporary:
        work = Path(temporary)
        audio_segments = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=config.get("browser_args", []))
            context = browser.new_context(storage_state=config.get('storage_state'), viewport={'width': 1440, 'height': 900}, record_video_dir=str(work), record_video_size={'width': 1440, 'height': 900})
            page = context.new_page()
            started = time.monotonic()
            for index, scene in enumerate(config['scenes']):
                narration = work / f'{index}.txt'
                narration.write_text(scene['narration'])
                spoken = work / f'{index}.aiff'
                run(['say', '-v', config.get('voice', 'Samantha'), '-r', '165', '-f', str(narration), '-o', str(spoken)])
                silence = max(0, time.monotonic() - started)
                if silence:
                    padding = work / f'{index}-silence.wav'
                    run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', str(silence), str(padding)])
                    audio_segments.append(padding)
                scene_started = time.monotonic()
                if 'ci_repo' in scene:
                    revision = run(['git', 'rev-parse', 'HEAD']).strip()
                    remote = run(['git', 'ls-remote', 'origin', 'refs/heads/main']).strip().split()
                    if remote and remote[0] == revision:
                        raise RuntimeError('Commit the pending project changes before recording; HEAD is already published')
                    run(['git', 'push', 'origin', 'main'])
                    workflow = None
                    deadline = time.monotonic() + 900
                    while time.monotonic() < deadline:
                        runs = json.loads(run(['gh', 'run', 'list', '--repo', scene['ci_repo'], '--commit', revision, '--limit', '1', '--json', 'databaseId']))
                        if runs:
                            workflow = runs[0]['databaseId']
                            break
                        page.wait_for_timeout(3000)
                    if workflow is None:
                        raise RuntimeError('No workflow appeared for the pushed revision')
                    page.goto(f"https://github.com/{scene['ci_repo']}/actions/runs/{workflow}")
                    while time.monotonic() < deadline:
                        status = json.loads(run(['gh', 'run', 'view', str(workflow), '--repo', scene['ci_repo'], '--json', 'status,conclusion']))
                        if status['status'] == 'completed':
                            if status['conclusion'] != 'success':
                                raise RuntimeError(f'Workflow {workflow} did not pass')
                            page.reload()
                            page.wait_for_timeout(5000)
                            break
                        page.wait_for_timeout(10000)
                        page.reload()
                    else:
                        raise TimeoutError('Workflow did not finish within 15 minutes')
                elif 'image' in scene:
                    import base64
                    encoded = base64.b64encode(Path(scene['image']).read_bytes()).decode()
                    page.set_content(f'<html><body style="margin:0;background:#101f25;display:grid;place-items:center;height:100vh"><img style="max-width:100%;max-height:100vh" src="data:image/png;base64,{encoded}"></body></html>')
                elif 'url' in scene:
                    page.goto(scene['url'], wait_until='domcontentloaded')
                elif 'command' in scene:
                    output = run(scene['command'])
                    page.set_content('<html><body style="background:#101f25;color:#e2ece8;padding:35px;font:18px system-ui"><h1>' + html.escape(scene['title']) + '</h1><pre style="white-space:pre-wrap;font:16px/1.5 monospace">$ ' + html.escape(' '.join(scene['command'])) + '\n' + html.escape(output) + '</pre></body></html>')
                elif 'html' in scene:
                    page.set_content(scene['html'])
                for action in scene.get('actions', []):
                    locator = page.locator(action['selector'])
                    if action['type'] == 'fill':
                        locator.fill(action['value'])
                    elif action['type'] == 'select':
                        locator.select_option(action['value'])
                    else:
                        locator.click()
                hold = max(scene.get('seconds', 0), duration(spoken) + 2)
                page.wait_for_timeout(max(0, hold - (time.monotonic() - scene_started)) * 1000)
                elapsed = time.monotonic() - scene_started
                segment = work / f'{index}-audio.wav'
                run(['ffmpeg', '-y', '-i', str(spoken), '-af', 'apad', '-t', str(elapsed), '-ar', '44100', '-ac', '1', str(segment)])
                audio_segments.append(segment)
                started = time.monotonic()
            video = Path(page.video.path())
            context.close()
            browser.close()
        manifest = work / 'audio.txt'
        manifest.write_text(''.join(f"file '{segment}'\n" for segment in audio_segments))
        run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(manifest), '-i', str(video), '-map', '1:v', '-map', '0:a', '-c:v', 'libx264', '-preset', 'fast', '-crf', '25', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', str(args.output)])
        print(json.dumps({'output': str(args.output), 'seconds': duration(args.output), 'narration': 'Synthetic macOS voice', 'scenes': len(config['scenes'])}))


if __name__ == '__main__':
    main()
