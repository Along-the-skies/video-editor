FIRST_LAST_DURATION = 3.0
IMAGE_MIN = 3.0
IMAGE_MAX = 7.0
VIDEO_MAX = 8.0

MIN_BOOKEND = 1.0 

def compute_timeline(audio_duration: float, middle_items: list[dict]) -> dict:
    first_duration = FIRST_LAST_DURATION
    last_duration = FIRST_LAST_DURATION

    video_items = [i for i in middle_items if i["kind"] == "video"]
    image_items = [i for i in middle_items if i["kind"] == "image"]
    video_durations = [min(v["duration"], VIDEO_MAX) for v in video_items]
    video_fixed_sum = sum(video_durations)

    available_for_video = audio_duration - 2 * MIN_BOOKEND
    if video_fixed_sum > available_for_video:
        if available_for_video <= 0:
            video_durations = [0 for _ in video_durations]
            video_fixed_sum = 0
            first_duration = audio_duration / 2
            last_duration = audio_duration / 2
        else:
            scale = available_for_video / video_fixed_sum
            video_durations = [v * scale for v in video_durations]
            video_fixed_sum = available_for_video
            first_duration = MIN_BOOKEND
            last_duration = MIN_BOOKEND

    remaining = audio_duration - first_duration - last_duration - video_fixed_sum
    n = len(image_items)

    if n == 0:
        last_duration += remaining
        image_durations = []
        included_items = middle_items
    elif remaining < IMAGE_MIN * n:
        leftover_for_bookends = audio_duration - video_fixed_sum
        first_duration = leftover_for_bookends / 2
        last_duration = leftover_for_bookends / 2
        image_durations = []
        included_items = video_items
    else:
        base = remaining / n
        clamped = [max(IMAGE_MIN, min(IMAGE_MAX, base)) for _ in range(n)]
        leftover = remaining - sum(clamped)
        last_duration += leftover
        image_durations = clamped
        included_items = middle_items

    middle_result = []
    vi, ii = 0, 0
    for item in included_items:
        if item["kind"] == "video":
            middle_result.append((item, video_durations[vi]))
            vi += 1
        else:
            middle_result.append((item, image_durations[ii]))
            ii += 1

    return {"first": first_duration, "last": last_duration, "middle": middle_result}