from celery import shared_task


@shared_task
def process_resume_task(resume_id):
    from .models import Resume
    from .services import process_resume

    resume = Resume.objects.filter(id=resume_id).first()
    if resume:
        process_resume(resume)
        # warm up the live-job cache for this user in the background
        from jobs.tasks import fetch_jobs_for_resume
        fetch_jobs_for_resume.delay(resume_id)
