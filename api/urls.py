from django.urls import path
from .views import api_home, create_complaint ,detect_waste_type, download_all_images, manager_mark_completed,manager_pending_complaints,signup, login, contractor_complaints, assign_complaints, karmachari_complaints, submit_karmachari_work, complaint_image, contractor_completed_complaints, submit_to_manager
from .views import create_complaint, citizen_complaints


urlpatterns = [
    path('', api_home),
    path("complaint/create/", create_complaint),
    path("detect-waste/", detect_waste_type),
    path("download/images/", download_all_images),
    path("signup/", signup),
    path("login/", login),
    path("contractor/complaints/", contractor_complaints),
    path("assign-complaints/", assign_complaints),
    path("karmachari/complaints/<str:karmachari_id>/", karmachari_complaints),
    path("karmachari/submit-work/", submit_karmachari_work),
    path("complaint/image/<str:complaint_id>/<str:image_type>/", complaint_image),
    path("contractor/completed/<str:contractor_id>/", contractor_completed_complaints),
    path("contractor/submit-manager/", submit_to_manager),
    path("manager/complaints/", manager_pending_complaints),
    path("manager/mark-completed/", manager_mark_completed),
    path("citizen/complaints/<str:citizen_id>/", citizen_complaints),

]
