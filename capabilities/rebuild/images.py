"""Strict capture comparison; Pillow is needed only for image requirements."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
from .contracts import local_file


def srgb_image(image):
    from PIL import ImageCms
    profile = image.info.get('icc_profile')
    if profile:
        source = ImageCms.ImageCmsProfile(BytesIO(profile))
        return ImageCms.profileToProfile(image, source, ImageCms.createProfile('sRGB'), outputMode='RGB')
    return image.convert('RGB')


def profile_facts(image):
    from PIL import ImageCms
    profile = image.info.get('icc_profile')
    return {'input_profile': ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(BytesIO(profile))).strip() if profile else 'untagged browser CSS capture; assumed sRGB',
            'input_profile_sha256': hashlib.sha256(profile).hexdigest() if profile else None,
            'comparison_space': 'sRGB'}


def compare_capture(root, requirement, state):
    root = Path(root).resolve()
    try:
        from PIL import Image, ImageChops, ImageStat, ImageCms
    except ImportError:
        return {'status': 'unavailable', 'reason': 'Pillow is required for image_pixels comparison'}
    reference_path = local_file(root, requirement['reference_image'])
    pixels = requirement['pixels']
    if not isinstance(pixels, list) or len(pixels) != 2 or any(type(v) is not int or v <= 0 for v in pixels):
        raise ValueError('Invalid reference image dimensions')
    capture = state.get('capture')
    if not isinstance(capture, dict) or not isinstance(capture.get('path'), str):
        return {'status': 'unavailable', 'reason': 'Driver did not collect a capture file'}
    candidate_path = local_file(root, capture['path'], must_exist=False)
    rect, scale, window = (capture.get(k) for k in ('content_rect_points', 'backing_scale', 'window_points'))
    finite = lambda v: type(v) in (int, float) and math.isfinite(v)
    if (not isinstance(rect, list) or len(rect) != 4 or not all(finite(v) for v in rect)
            or rect[0] < 0 or rect[1] < 0 or rect[2:] != pixels
            or not finite(scale) or scale <= 0 or not isinstance(window, list) or len(window) != 2
            or not all(finite(v) and v > 0 for v in window)
            or rect[0] + rect[2] > window[0] or rect[1] + rect[3] > window[1]):
        return {'status': 'unavailable', 'reason': 'Missing or incompatible measured capture geometry'}
    try:
        with Image.open(reference_path) as im:
            if im.size != tuple(pixels):
                raise ValueError('Reference image does not match frozen viewport')
            reference_profile = profile_facts(im)
            reference = srgb_image(im)
        with Image.open(candidate_path) as im:
            if im.size != tuple(round(v * scale) for v in window):
                return {'status': 'unavailable', 'reason': 'Capture size does not match measured window and scale'}
            candidate_profile = profile_facts(im)
            x, y, w, h = rect
            candidate = srgb_image(im).crop(tuple(round(v * scale) for v in (x, y, x+w, y+h)))
            candidate = candidate.resize(tuple(pixels), Image.Resampling.LANCZOS)
    except (OSError, ImageCms.PyCMSError) as error:
        return {'status': 'unavailable', 'reason': 'Capture decoding/color conversion failed: ' + type(error).__name__}
    difference = ImageChops.difference(reference, candidate)
    return {'status': 'pass' if all(hi == 0 for lo, hi in difference.getextrema()) else 'fail',
            'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
            'capture_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            'mean_absolute_rgb_difference': ImageStat.Stat(difference).mean,
            'profiles': {'reference': reference_profile, 'candidate': candidate_profile},
            'normalization': 'ICC to sRGB; measured titlebar crop and backing-scale downsample; no masks, alignment search or tolerance',
            'reason': 'Actual same-state image pixels only; sound, animation timing and unvisited states remain separate'}
