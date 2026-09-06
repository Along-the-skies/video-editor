FIRST_LAST_DURATION = 3.0
IMAGE_MIN = 3.0
IMAGE_MAX = 7.0
VIDEO_MAX = 8.0

MIN_BOOKEND = 1.0


def compute_timeline(audio_duration: float, middle_items: list[dict]) -> dict:
    video_items = [i for i in middle_items if i["kind"] == "video"]
    image_items = [i for i in middle_items if i["kind"] == "image"]

    n_images = len(image_items)
    natural_video_durations = [min(v["duration"], VIDEO_MAX) for v in video_items]
    natural_video_sum = sum(natural_video_durations)
    image_min_total = IMAGE_MIN * n_images

    first_duration = FIRST_LAST_DURATION
    last_duration = FIRST_LAST_DURATION
    bookend_total = first_duration + last_duration

    remaining = audio_duration - bookend_total - image_min_total - natural_video_sum

    if remaining < 0:
        first_duration = MIN_BOOKEND
        last_duration = MIN_BOOKEND
        bookend_total = first_duration + last_duration
        remaining = audio_duration - bookend_total - image_min_total - natural_video_sum

    if remaining >= 0:
        video_durations = natural_video_durations
        if n_images > 0:
            extra_budget = IMAGE_MAX - IMAGE_MIN
            per_image_extra = min(extra_budget, remaining / n_images)
            image_durations = [IMAGE_MIN + per_image_extra for _ in range(n_images)]
            used_extra = per_image_extra * n_images
            last_duration += remaining - used_extra
        else:
            image_durations = []
            last_duration += remaining
    else:
        available_for_video = audio_duration - bookend_total - image_min_total

        if available_for_video > 0:
            scale = available_for_video / natural_video_sum if natural_video_sum > 0 else 0
            video_durations = [v * scale for v in natural_video_durations]
            image_durations = [IMAGE_MIN for _ in range(n_images)]
        else:
            video_durations = [0 for _ in natural_video_durations]
            available_for_images_and_bookends = audio_duration

            if image_min_total <= available_for_images_and_bookends:
                leftover_for_bookends = available_for_images_and_bookends - image_min_total
                first_duration = leftover_for_bookends / 2
                last_duration = leftover_for_bookends / 2
                image_durations = [IMAGE_MIN for _ in range(n_images)]
            else:
                first_duration = 0
                last_duration = 0
                scale = available_for_images_and_bookends / image_min_total if image_min_total > 0 else 0
                image_durations = [IMAGE_MIN * scale for _ in range(n_images)]

    middle_result = []
    vi, ii = 0, 0
    for item in middle_items:
        if item["kind"] == "video":
            duration = video_durations[vi]
            vi += 1
            if duration > 0.05:
                middle_result.append((item, duration))
        else:
            duration = image_durations[ii]
            ii += 1
            middle_result.append((item, duration))

    return {"first": first_duration, "last": last_duration, "middle": middle_result}