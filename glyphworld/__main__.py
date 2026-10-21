import argparse
import json
import sys
import time
from pathlib import Path
from .config import load_config, ROOT


def main():
    parser = argparse.ArgumentParser(description="GlyphWorld 0.2 — The Forgotten City")
    parser.add_argument("--config", type=Path, default=ROOT / "config.toml")
    parser.add_argument("--frames", type=int, default=0, help="Exit after N frames; 0 runs until closed")
    parser.add_argument("--benchmark", type=Path, help="Write measured frame times and hardware metadata")
    parser.add_argument("--capture", type=Path, help="Save last frame before swap")
    parser.add_argument("--hidden", action="store_true", help="Hidden GLFW window for automated GPU smoke test")
    parser.add_argument("--no-vsync", action="store_true")
    args = parser.parse_args()
    if args.frames < 0 or (args.hidden and args.frames == 0):
        parser.error("--frames must be nonnegative; --hidden requires a finite --frames")
    config = load_config(args.config)
    try:
        import glfw
        import moderngl
        from .renderer import Renderer
        from .metrics import Metrics
    except ImportError as error:
        raise RuntimeError("Install dependencies: python -m pip install -r requirements.txt") from error
    from .camera import Camera
    from .character import Character
    from .lighting import Atmosphere
    glfw.set_error_callback(lambda code, message: print(f"GLFW {code}: {message}", file=sys.stderr))
    if not glfw.init():
        raise RuntimeError("GLFW initialization failed; a desktop session and OpenGL 3.3 are required")
    window = ctx = renderer = None
    try:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.VISIBLE, not args.hidden)
        window = glfw.create_window(config.width, config.height, "GlyphWorld | The Forgotten City", None, None)
        if not window:
            raise RuntimeError("Could not open an OpenGL 3.3 window. Check the graphics driver.")
        glfw.make_context_current(window)
        glfw.swap_interval(int(config.vsync and not args.no_vsync))
        ctx = moderngl.create_context(require=330)
        renderer = Renderer(ctx, config)
        camera = Camera(zoom=config.zoom)
        character = Character()
        atmosphere = Atmosphere(config.rain, config.lighting)
        metrics = Metrics()
        state = {"paused": False, "metrics": True, "capture": False}

        def on_key(win, key, scancode, action, mods):
            if action != glfw.PRESS:
                return
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(win, True)
            elif key == glfw.KEY_SPACE:
                state["paused"] = not state["paused"]
            elif key == glfw.KEY_R:
                atmosphere.rain = not atmosphere.rain
                renderer.history_valid = False
            elif key == glfw.KEY_L:
                atmosphere.lighting = not atmosphere.lighting
                renderer.history_valid = False
            elif key == glfw.KEY_F1:
                state["metrics"] = not state["metrics"]
            elif key == glfw.KEY_F2:
                renderer.debug = (renderer.debug + 1) % 5
            elif key == glfw.KEY_LEFT_BRACKET:
                renderer.density(-1)
            elif key == glfw.KEY_RIGHT_BRACKET:
                renderer.density(1)
            elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
                camera.zoom_by(1.1)
            elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
                camera.zoom_by(1/1.1)
            elif key == glfw.KEY_F12:
                state["capture"] = True

        glfw.set_key_callback(window, on_key)
        glfw.set_scroll_callback(window, lambda win, x, y: camera.zoom_by(1.1**y))
        print("OpenGL:", ctx.info.get("GL_RENDERER"), ctx.info.get("GL_VERSION"))
        print("Space pause | [ ] density | R rain | L light | F1 metrics | F2 maps | +/- zoom | F12 capture")
        previous = time.perf_counter()
        title_time, frames = 0.0, 0
        while not glfw.window_should_close(window):
            frame_start = time.perf_counter()
            dt = min(frame_start-previous, .05)
            previous = frame_start
            glfw.poll_events()
            size = glfw.get_framebuffer_size(window)
            if min(size) == 0:
                glfw.wait_events_timeout(.1)
                continue
            if size != renderer.size:
                renderer.resize(*size)
            if not state["paused"]:
                character.update(dt)
                camera.update(character.x, dt)
                atmosphere.update(dt)
            renderer.render(camera, character, atmosphere)
            frames += 1
            if state["capture"]:
                renderer.capture(ROOT / "captures" / f"glyphworld-{time.time_ns()}.png")
                state["capture"] = False
            if args.capture and args.frames and frames == args.frames:
                renderer.capture(args.capture)
            glfw.swap_buffers(window)
            if args.benchmark:
                ctx.finish()  # Include GPU completion rather than just CPU submission.
            metrics.add(time.perf_counter()-frame_start)
            if frame_start-title_time>.5:
                s = metrics.summary()
                title = "GlyphWorld 0.2 | The Forgotten City"
                if state["metrics"]:
                    title += (f" | {s['fps']:.1f} FPS / {s['frame_ms']:.2f} ms"
                              f" | {renderer.grid[0]*renderer.grid[1]:,} glyphs"
                              f" | RAM {s['rss_mib']:.0f} MiB / textures ~{renderer.gpu_bytes/1024**2:.1f} MiB"
                              f" | map {renderer.debug}" + (" | PAUSED" if state["paused"] else ""))
                glfw.set_window_title(window, title)
                title_time = frame_start
            if args.frames and frames >= args.frames:
                break
        if args.benchmark:
            report = {**metrics.summary(), "total_frames": frames, "renderer": ctx.info.get("GL_RENDERER"),
                      "vendor": ctx.info.get("GL_VENDOR"), "opengl": ctx.info.get("GL_VERSION"),
                      "resolution": renderer.size, "grid": renderer.grid,
                      "texture_mib_estimate": renderer.gpu_bytes/1024**2,
                      "vsync": config.vsync and not args.no_vsync,
                      "sample_window": "last up to 600 frames, including present and GPU finish",
                      "frame_ms_samples": [x*1000 for x in metrics.samples]}
            args.benchmark.parent.mkdir(parents=True, exist_ok=True)
            args.benchmark.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps({k:v for k,v in report.items() if k != "frame_ms_samples"}, indent=2))
    finally:
        if renderer:
            renderer.release()
        if ctx:
            ctx.release()
        if window:
            glfw.destroy_window(window)
        glfw.terminate()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(f"GlyphWorld: {error}", file=sys.stderr)
        sys.exit(1)
