def run_pipeline(emotion, index, mode="all"):
    job = {
        "input_emotion": emotion,
        "emotion": emotion
    }

    if mode in ["image", "all"]:
        from app.stages.image import image_stage
        job = image_stage(job, index)

    if mode in ["luma", "all"]:
        from app.stages.luma_prompt import luma_prompt_stage
        job = luma_prompt_stage(job)

    return job
