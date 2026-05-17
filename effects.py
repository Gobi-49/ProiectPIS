import cv2
import numpy as np


def apply_brightness_contrast(frame, brightness=0, contrast=1.0):
    result = frame.astype(np.float32)
    result = result * contrast + brightness
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_saturation(frame, saturation=1.0):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= saturation
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_film_grain(frame, intensity=10):
    if intensity <= 0:
        return frame

    noise = np.random.normal(0, intensity, frame.shape).astype(np.float32)
    result = frame.astype(np.float32) + noise
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_vignette(frame, amount=0.5):
    if amount <= 0:
        return frame

    rows, cols = frame.shape[:2]

    x_kernel = cv2.getGaussianKernel(cols, cols * 0.6)
    y_kernel = cv2.getGaussianKernel(rows, rows * 0.6)
    kernel = y_kernel @ x_kernel.T

    mask = kernel / kernel.max()
    mask = 1 - amount * (1 - mask)

    result = frame.astype(np.float32)
    result[:, :, 0] *= mask
    result[:, :, 1] *= mask
    result[:, :, 2] *= mask

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_chromatic_aberration(frame, amount=2):
    if amount <= 0:
        return frame

    b, g, r = cv2.split(frame)

    r = np.roll(r, amount, axis=1)
    b = np.roll(b, -amount, axis=1)

    return cv2.merge([b, g, r])


def apply_pixelation(frame, pixel_size=1):
    if pixel_size <= 1:
        return frame

    h, w = frame.shape[:2]

    small = cv2.resize(
        frame,
        (max(1, w // pixel_size), max(1, h // pixel_size)),
        interpolation=cv2.INTER_LINEAR
    )

    pixelated = cv2.resize(
        small,
        (w, h),
        interpolation=cv2.INTER_NEAREST
    )

    return pixelated


def apply_vintage(frame, strength=0.0):
    if strength <= 0:
        return frame

    img = frame.astype(np.float32)

    # Tonuri calde / vintage
    img[:, :, 0] *= 1.0 - 0.2 * strength  # blue
    img[:, :, 1] *= 1.0 + 0.05 * strength # green
    img[:, :, 2] *= 1.0 + 0.25 * strength # red

    # contrast ușor redus
    img = (img - 128) * (1.0 - 0.25 * strength) + 128

    # imagine ușor faded
    img = img + 20 * strength

    return np.clip(img, 0, 255).astype(np.uint8)


def apply_effect_pipeline(
    frame,
    brightness=0,
    contrast=1.0,
    saturation=1.0,
    grain=0,
    vignette=0.0,
    chromatic=0,
    pixel_size=1,
    vintage=0.0
):
    result = frame.copy()

    result = apply_brightness_contrast(result, brightness, contrast)
    result = apply_saturation(result, saturation)
    result = apply_vintage(result, vintage)
    result = apply_chromatic_aberration(result, chromatic)
    result = apply_pixelation(result, pixel_size)
    result = apply_vignette(result, vignette)
    result = apply_film_grain(result, grain)

    return result