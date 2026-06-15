import pytest

from sermoncut_core import io_utils
from sermoncut_core.render import (
    crop_filter,
    build_ffmpeg_command,
    render_short,
)


@pytest.fixture
def project(tmp_path):
    io_utils.set_project(tmp_path)
    return tmp_path


def test_crop_filter_variants():
    assert crop_filter("center") == "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920"
    assert crop_filter("left").endswith("crop=ih*9/16:ih:0:0,scale=1080:1920")
    assert "iw-ih*9/16:0" in crop_filter("right")


def test_crop_filter_invalid():
    with pytest.raises(ValueError):
        crop_filter("middle")


def test_build_command_structure():
    cmd = build_ffmpeg_command("in.mp4", 100.0, 125.0, "out.mp4", crop="center")
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd and "100.000" in cmd
    assert "25.000" in cmd          # duration = end-start
    assert "1080:1920" in cmd[cmd.index("-vf") + 1]
    assert cmd[-1] == "out.mp4"
    assert "libx264" in cmd


def test_build_command_with_subtitles():
    cmd = build_ffmpeg_command("in.mp4", 0.0, 20.0, "o.mp4", subtitle_path="C:/x/clip.srt")
    vf = cmd[cmd.index("-vf") + 1]
    assert "subtitles=" in vf
    assert "force_style=" in vf


def test_build_command_fit_blur_uses_filter_complex():
    cmd = build_ffmpeg_command("in.mp4", 0.0, 20.0, "o.mp4", crop="fit")
    assert "-filter_complex" in cmd
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "split=2" in fc and "boxblur" in fc and "overlay=" in fc
    assert "-map" in cmd and "[vout]" in cmd


def test_build_command_fit_blur_with_subtitles():
    cmd = build_ffmpeg_command("in.mp4", 0.0, 20.0, "o.mp4", crop="fit", subtitle_path="c.srt")
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "subtitles=" in fc and "[vout]" in fc


def test_build_command_fit_black_pads():
    cmd = build_ffmpeg_command("in.mp4", 0.0, 20.0, "o.mp4", crop="fit_black")
    vf = cmd[cmd.index("-vf") + 1]
    assert "pad=1080:1920" in vf and "decrease" in vf


def test_render_short_success_updates_status(project):
    job = {
        "id": "short_001", "candidate_id": "cand_001",
        "source_start": 100.0, "source_end": 125.0,
        "crop": "center", "output_path": "output/short_001.mp4",
        "status": "pending", "progress": 0,
    }
    out = render_short(job, "in.mp4", runner=lambda _argv: 0)
    assert out["status"] == "done"
    assert out["progress"] == 100


def test_render_short_failure(project):
    job = {
        "id": "short_002", "candidate_id": "cand_002",
        "source_start": 0.0, "source_end": 20.0,
        "crop": "left", "output_path": "output/short_002.mp4",
        "status": "pending", "progress": 0,
    }
    out = render_short(job, "in.mp4", runner=lambda _argv: 1)
    assert out["status"] == "failed"
