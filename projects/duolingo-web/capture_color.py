"""Normalize tagged display captures to the browser reference's sRGB space."""
import hashlib
from io import BytesIO
from PIL import ImageCms


def srgb_image(image):
    profile = image.info.get('icc_profile')
    if profile:
        source = ImageCms.ImageCmsProfile(BytesIO(profile))
        return ImageCms.profileToProfile(image, source, ImageCms.createProfile('sRGB'), outputMode='RGB')
    # The untagged browser PNG is the CSS/sRGB reference; record this assumption.
    return image.convert('RGB')


def profile_facts(image):
    profile = image.info.get('icc_profile')
    return {'input_profile': ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(BytesIO(profile))).strip() if profile else 'untagged browser CSS capture; assumed sRGB',
            'input_profile_sha256': hashlib.sha256(profile).hexdigest() if profile else None,
            'comparison_space': 'sRGB'}
