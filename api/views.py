from django.shortcuts import render


from django.http import JsonResponse

def api_home(request):
    return JsonResponse({
        "message": "API working successfully 🚀"
    })


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from .models import Complaint, ComplaintWorkflowLog, StaffUser, User
import sib_api_v3_sdk
from django.conf import settings






import sib_api_v3_sdk
from django.conf import settings

def normalize_area(area: str):
    return area.lower().replace(" ", "").replace("school", "")

def send_complaint_completed_email(email, username, complaint_no):
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY

    api = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(config)
    )

    email_data = sib_api_v3_sdk.SendSmtpEmail(
        subject=f"✅ Complaint #{complaint_no} Completed",
        html_content=f"""
        <h3>Hello {username},</h3>

        <p>Good news 🎉</p>

        <p>Your complaint has been <b>successfully resolved</b>.</p>

        <p><b>Complaint No:</b> {complaint_no}</p>
        <p><b>Status:</b> Completed</p>

        <p>Thank you for helping keep our city clean.</p>

        <br>
        <p>Regards,<br><b>Bravo Support Team</b></p>
        """,
        sender={
            "name": "Bravo Support",
            "email": "project4950@gmail.com"  # ✅ VERIFIED SENDER
        },
        to=[{"email": email}],
    )

    response = api.send_transac_email(email_data)
    print("Completion email response:", response)



import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def health_check(request):
    logger.info("Health check endpoint hit")
    return JsonResponse({"status": "ok"})




def send_complaint_confirmation_email(email, username, complaint_id, complaint_no):
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = settings.BREVO_API_KEY

    api = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(config)
    )

    email_data = sib_api_v3_sdk.SendSmtpEmail(
        subject=f"✅ Complaint #{complaint_no} Registered",
        html_content=f"""
        <h3>Hello {username}</h3>
        <p>Your complaint has been registered successfully.</p>
        <p><b>Complaint No:</b> {complaint_no}</p>
        <p><b>Complaint ID:</b> {complaint_id}</p>
        """,
        sender={"name": "Bravo Support", "email": "project4950@gmail.com"},
        to=[{"email": email}],
    )

    response = api.send_transac_email(email_data)
    print("Brevo response:", response)



@api_view(["POST"])
def create_complaint(request):
    citizen_id = request.data.get("citizen_id")
    title = request.data.get("title")
    description = request.data.get("description")
    area = request.data.get("area")
    waste_type = request.data.get("waste_type")
    image = request.FILES.get("before_image")

    if not all([citizen_id, title, description, area, image]):
        return Response({"message": "Missing required fields"}, status=400)

    area = area.strip()
    normalized_area = normalize_area(area)

    # ✅ FIXED: syntax + use proper field name
    contractor = StaffUser.objects(
        user_role="CONTRACTOR"
    ).filter(
        assigned_area__icontains=area  # or normalized_area if DB normalized
    ).first()

    if not contractor:
        return Response(
            {"message": f"No contractor found for area {area}"},
            status=400
        )

    complaint = Complaint(
        complaint_no=get_next_complaint_no(),
        citizen_id=citizen_id,
        title=title,
        description=description,
        area=area,
        waste_type=waste_type,
        status="PENDING",
        before_image=image,
        assigned_contractor=contractor
    )
    complaint.save()

    # ✅ SEND EMAIL
    try:
        user = User.objects(id=citizen_id).first()
        if user:
            send_complaint_confirmation_email(
                email=user.email,
                username=user.username,
                complaint_id=str(complaint.id),
                complaint_no=complaint.complaint_no
            )
    except Exception as e:
        print("Email error:", e)

    return Response({
        "message": "✅ Complaint registered & assigned",
        "complaint_id": str(complaint.id),
        "complaint_no": complaint.complaint_no,
        "contractor": contractor.full_name
    }, status=201)


    



import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

HF_MODEL_URL = "https://router.huggingface.co/hf-inference/models/WinKawaks/vit-tiny-patch16-224"
import os

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")



@csrf_exempt
def detect_waste_type(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    if "image" not in request.FILES:
        return JsonResponse({"error": "Image file required"}, status=400)

    image_file = request.FILES["image"]

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": image_file.content_type or "image/jpeg"
    }

    # Call Hugging Face API
    response = requests.post(
        HF_MODEL_URL,
        headers=headers,
        data=image_file.read(),
        timeout=30
    )

    if response.status_code != 200:
        return JsonResponse(
            {"error": "Hugging Face API failed", "details": response.text},
            status=500
        )

    predictions = response.json()

    # -------------------------------
    # Score accumulators
    # -------------------------------
    plastic_score = 0
    dry_score = 0
    wet_score = 0
    medical_score = 0

    all_labels = []

    for item in predictions:
        label = item.get("label", "").lower()
        score = float(item.get("score", 0))

        all_labels.append(f"{label.title()} - {round(score * 100, 2)}")

        if "plastic" in label or "packet" in label:
            plastic_score += score

        elif any(k in label for k in ["can", "ashcan", "dustbin"]):
            dry_score += score

        elif any(k in label for k in [
            "food", "fruit", "vegetable", "cabbage", "plate", "hot pot"
        ]):
            wet_score += score

        elif any(k in label for k in ["medical", "syringe", "mask"]):
            medical_score += score

    # -------------------------------
    # Final category decision
    # -------------------------------
    if plastic_score >= dry_score and plastic_score >= wet_score and plastic_score >= medical_score:
        category = "Plastic Waste"
    elif dry_score >= wet_score and dry_score >= medical_score:
        category = "Dry Waste"
    elif wet_score >= medical_score:
        category = "Wet Waste"
    else:
        category = "Medical Waste"

    return JsonResponse({
        "waste_type": category,
        "debug_scores": {
            "plastic": round(plastic_score, 4),
            "dry": round(dry_score, 4),
            "wet": round(wet_score, 4),
            "medical": round(medical_score, 4)
        },
        "labels_detected": all_labels
    })



import zipfile
import io
from django.http import HttpResponse
from .models import Complaint


def download_all_images(request):
    """
    Download all BEFORE images of complaints as a ZIP file
    """

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        complaints = Complaint.objects(before_image__ne=None)

        for idx, complaint in enumerate(complaints, start=1):
            image = complaint.before_image

            if not image:
                continue

            # read image bytes
            image.seek(0)
            image_bytes = image.read()

            # filename inside zip
            filename = f"complaint_{idx}_{complaint.id}.jpg"

            zip_file.writestr(filename, image_bytes)

    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type="application/zip"
    )
    response["Content-Disposition"] = 'attachment; filename="complaint_images.zip"'

    return response

from django.http import HttpResponse

from django.http import HttpResponse
from bson import ObjectId
from .models import Complaint

def complaint_image(request, complaint_id, image_type):
    complaint = Complaint.objects(id=ObjectId(complaint_id)).first()

    if not complaint:
        return HttpResponse(status=404)

    if image_type == "before":
        image = complaint.before_image
    elif image_type == "after":
        image = complaint.after_image
    else:
        return HttpResponse(status=400)

    if not image or not getattr(image, "grid_id", None):
        return HttpResponse(status=404)

    image.seek(0)
    return HttpResponse(image.read(), content_type="image/jpeg")




from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from .models import User

@api_view(["POST"])
def signup(request):
    data = request.data

    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")
    email = data.get("email")

    if not all([username, password, phone, email]):
        return Response({"message": "All fields required"}, status=400)

    if User.objects(email=email).first():
        return Response({"message": "Email already exists"}, status=400)

    User(
        username=username,
        password=make_password(password),
        phone=phone,
        email=email,
    ).save()

    return Response({"message": "Signup successful"}, status=201)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import User, StaffUser, SafaiKarmachari

@api_view(["POST"])
def login(request):
    phone = request.data.get("phone")
    username = request.data.get("username")
    password = request.data.get("password")

    if not all([phone, username, password]):
        return Response(
            {"message": "Phone, username and password are required"},
            status=400
        )

    # 1️⃣ USER / CITIZEN
    user = User.objects(phone=phone, username=username).first()
    if user and check_password(password, user.password):
        return Response({
            "role": "CITIZEN",
            "user_id": str(user.id),
            "name": user.username,
            "email": user.email,
            "redirect": "/submit-complaint"
        })

    # 2️⃣ STAFF USERS
    staff = StaffUser.objects(
        phone_number=phone,
        full_name=username
    ).first()

    if staff and check_password(password, staff.password):
        redirect_map = {
            "ADMIN": "/admin-dashboard",
            "MANAGER": "/manager-dashboard",
            "CONTRACTOR": "/contractor-dashboard",
            "SAFAI KARMCHARI": "/karmachari-dashboard",
        }

        return Response({
            "role": staff.user_role,
            "user_id": str(staff.id),
            "name": staff.full_name,
            "area": staff.assigned_area,
            "redirect": redirect_map.get(staff.user_role)
        })

    # 3️⃣ SAFAI KARMACHARI ✅ FIXED
    karma = SafaiKarmachari.objects(
        phone_no=phone,
        username=username
    ).first()

    if karma and check_password(password, karma.password):
        return Response({
            "role": "SAFAI KARMCHARI",
            "user_id": str(karma.id),
            "name": karma.username,
            "area": karma.area,
            "redirect": "/karmachari-dashboard"
        })

    # 4️⃣ INVALID
    return Response(
        {"message": "Invalid phone number, username, or password"},
        status=401
    )


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Complaint

@api_view(["GET"])
def contractor_complaints(request, contractor_id):
    try:
        complaints = Complaint.objects(assigned_contractor=contractor_id, assigned_karmachari=None)

        data = []

        for c in complaints:
            before_url = None

            if c.before_image and getattr(c.before_image, "grid_id", None):
                before_url = (f"https://backend-009.onrender.com/api/complaint/image/{c.id}/before/")

            data.append({
                "id": str(c.id),
                "complaint_no": c.complaint_no,
                "title": c.title,
                "area": c.area,
                "status": c.status,
                "before_image_url": before_url
            })

        # ✅ RETURN AFTER LOOP
        return Response(data)

    except Exception as e:
        print("❌ contractor_complaints ERROR:", e)
        return Response(
            {"message": "Server error while loading complaints"},
            status=500
        )


def get_area_key(area: str):
    """
    Normalize all area names to stable keys
    """
    if not area:
        return ""

    area = area.lower()

    if "dn" in area:
        return "dn"
    if "mb" in area:
        return "mb"
    if "svp" in area:
        return "svp"
    if "mahatma" in area or "gandhi" in area:
        return "mgv"

    return area.replace(" ", "")


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Complaint, SafaiKarmachari

@api_view(["POST"])
def assign_complaints(request):
    complaint_ids = request.data.get("complaint_ids", [])
    

    if not complaint_ids:
        return Response({"message": "No complaints selected"}, status=400)

    assigned_count = 0

    for cid in complaint_ids:
        # 1️⃣ Get complaint (not already assigned)

        try:
            cid = ObjectId(cid)   # ✅ CRITICAL FIX
        except Exception:
            continue
        
        complaint = Complaint.objects(
            id=cid,
            assigned_karmachari=None
        ).first()

        if not complaint:
            continue

        # 2️⃣ Find FREE karmachari in same area
        complaint_area_key = get_area_key(complaint.area)

        karmachari = None
        for k in SafaiKarmachari.objects(status="FREE"):
            if get_area_key(k.area) == complaint_area_key:
                karmachari = k
                break

        if not karmachari:
            continue

        # 3️⃣ Assign complaint
        complaint.assigned_karmachari = karmachari
        complaint.status = "IN PROGRESS"
        complaint.due_date = timezone.now() + timedelta(days=2)
        complaint.save()

        # 4️⃣ Update karmachari status
        karmachari.status = "WORKING"
        karmachari.save()

        assigned_count += 1

    return Response({
        "message": f"✅ {assigned_count} complaint(s) assigned to Safai Karmachari"
    })






from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Complaint

@api_view(["GET"])
def karmachari_complaints(request, karmachari_id):
    try:
        karmachari_oid = ObjectId(karmachari_id)
    except Exception:
        return Response({"message": "Invalid karmachari ID"}, status=400)

    complaints = Complaint.objects(
        assigned_karmachari=karmachari_oid,
        status="IN PROGRESS"
    )

    data = []
    for c in complaints:
        before_url = None
        if c.before_image and getattr(c.before_image, "grid_id", None):
            before_url = f"https://backend-009.onrender.com/api/complaint/image/{c.id}/before/"

        data.append({
            "id": str(c.id),
            "title": c.title,
            "area": c.area,
            "before_image_url": before_url
        })

    return Response(data)



from django.utils import timezone
from .models import SafaiKarmachari

@api_view(["POST"])
def submit_karmachari_work(request):
    complaint_id = request.POST.get("complaint_id")
    karmachari_id = request.POST.get("karmachari_id")
    image = request.FILES.get("after_image")

    if not all([complaint_id, karmachari_id, image]):
        return Response({"message": "Missing data"}, status=400)

    complaint = Complaint.objects(id=complaint_id).first()
    karmachari = SafaiKarmachari.objects(id=karmachari_id).first()

    if not complaint or not karmachari:
        return Response({"message": "Invalid data"}, status=400)

    # ✅ Update complaint
    complaint.after_image = image
    complaint.status = "SUBMITTED"
    complaint.completion_date = timezone.now()
    complaint.save()

    # ✅ Free karmachari
    karmachari.status = "FREE"
    karmachari.save()

    return Response({"message": "✅ Work submitted successfully"})



from django.utils import timezone

@api_view(["POST"])
def submit_karmachari_work(request):
    complaint_id = request.POST.get("complaint_id")
    karmachari_id = request.POST.get("karmachari_id")
    image = request.FILES.get("after_image")

    if not all([complaint_id, karmachari_id, image]):
        return Response(
            {"message": "Missing data"},
            status=400
        )

    complaint = Complaint.objects(id=complaint_id).first()
    karmachari = SafaiKarmachari.objects(id=karmachari_id).first()

    if not complaint or not karmachari:
        return Response(
            {"message": "Invalid complaint or user"},
            status=400
        )

    # Update complaint
    complaint.after_image = image
    complaint.completion_date = timezone.now()
    complaint.status = "SUBMITTED"
    complaint.save()

    # Free karmachari
    karmachari.status = "FREE"
    karmachari.save()

    return Response({
        "message": "✅ Work submitted successfully"
    })


@api_view(["GET"])
def contractor_completed_complaints(request, contractor_id):
    complaints = Complaint.objects(
        assigned_contractor=contractor_id,
        status="SUBMITTED"
    )

    data = []
    for c in complaints:
        before_url = None
        after_url = None

        if c.before_image and getattr(c.before_image, "grid_id", None):
            before_url = f"https://backend-009.onrender.com/api/complaint/image/{c.id}/before/"

        if c.after_image and getattr(c.after_image, "grid_id", None):
            after_url = f"https://backend-009.onrender.com/api/complaint/image/{c.id}/after/"

        data.append({
            "id": str(c.id),
            "title": c.title,
            "area": c.area,
            "before_image_url": before_url,
            "after_image_url": after_url
        })

    return Response(data)


@api_view(["POST"])
def submit_to_manager(request):
    complaint_ids = request.data.get("complaint_ids", [])

    updated = 0
    for cid in complaint_ids:
        complaint = Complaint.objects(
            id=cid,
            status="SUBMITTED"
        ).first()

        if not complaint:
            continue

        complaint.status = "SENT_TO_MANAGER"
        complaint.save()
        updated += 1

    return Response({
        "message": f"✅ {updated} complaint(s) sent to Manager"
    })


@api_view(["GET"])
def manager_pending_complaints(request):
    complaints = Complaint.objects(status="SENT_TO_MANAGER")

    data = []

    for c in complaints:
        before_url = None
        after_url = None

        if c.before_image and getattr(c.before_image, "grid_id", None):
            before_url = f"https://backend-009.onrender.com/api/complaint/image/{c.id}/before/"

        if c.after_image and getattr(c.after_image, "grid_id", None):
            after_url = f"https://backend-009.onrender.com/api/complaint/image/{c.id}/after/"

        data.append({
            "id": str(c.id),
            "title": c.title,
            "area": c.area,
            "before_image_url": before_url,
            "after_image_url": after_url,
            "karmachari": {
                "id": str(c.assigned_karmachari.id) if c.assigned_karmachari else None,
                "name": c.assigned_karmachari.username if c.assigned_karmachari else None
            }
        })

    return Response(data)




@api_view(["POST"])
def manager_mark_completed(request):
    complaint_ids = request.data.get("complaint_ids", [])
    points = int(request.data.get("points", 10))  # default 10 points

    completed = 0

    for cid in complaint_ids:
        complaint = Complaint.objects(id=cid).first()

        if not complaint:
            continue

        # ✅ Mark complaint DONE
        complaint.status = "DONE"
        complaint.save()

        # ✅ FIXED: assigned_karmachari is already an object
        karmachari = complaint.assigned_karmachari
        if karmachari:
            karmachari.points = (karmachari.points or 0) + points
            karmachari.save()

        # ✅ Send completion email to citizen
        try:
            user = User.objects(id=complaint.citizen_id).first()
            if user:
                send_complaint_completed_email(
                    email=user.email,
                    username=user.username,
                    complaint_no=complaint.complaint_no
                )
        except Exception as e:
            print("Completion email error:", e)

        completed += 1

    return Response({
        "message": f"✅ {completed} complaint(s) marked as DONE"
    })



@api_view(["GET"])
def citizen_complaints(request, citizen_id):
    complaints = Complaint.objects(citizen_id=citizen_id).order_by("-complaint_date")

    data = []
    for c in complaints:
        data.append({
            "id": str(c.id),
            "complaint_no": c.complaint_no,
            "title": c.title,
            "area": c.area,
            "status": c.status.upper(),
            "complaint_date": c.complaint_date,
        })

    return Response(data)


from api.models import Counter

def get_next_complaint_no():
    counter = Counter.objects(name="complaint").modify(
        upsert=True,
        new=True,
        inc__value=1
    )
    return counter.value


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Complaint, SafaiKarmachari

@api_view(["GET"])
def admin_complaints_list(request):
    complaints = Complaint.objects().order_by("-complaint_date")

    data = []

    for c in complaints:
        karmachari = None

        if c.assigned_karmachari:
            karmachari = SafaiKarmachari.objects(
                id=c.assigned_karmachari.id
            ).first()

        data.append({
            "id": str(c.id),
            "complaint_no": c.complaint_no,
            "title": c.title,
            "area": c.area,
            "status": c.status,
            "karmachari": {
                "id": str(karmachari.id),
                "name": karmachari.username
            } if karmachari else None
        })

    return Response(data)



@api_view(["DELETE"])
def admin_delete_complaint(request, complaint_id):
    complaint = Complaint.objects(id=complaint_id).first()

    if not complaint:
        return Response(
            {"message": "Complaint not found"},
            status=404
        )

    # ✅ If complaint has assigned karmachari → FREE him
    if complaint.assigned_karmachari:
        karmachari = SafaiKarmachari.objects(
            id=complaint.assigned_karmachari.id
        ).first()

        if karmachari:
            karmachari.status = "FREE"
            karmachari.save()

    # ❌ Delete complaint
    complaint.delete()

    return Response({
        "message": "Complaint deleted and karmachari freed"
    })


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SafaiKarmachari, Complaint

@api_view(["GET"])
def admin_karmachari_list(request):
    karmacharis = SafaiKarmachari.objects()

    data = []

    for k in karmacharis:
        complaint = Complaint.objects(
            assigned_karmachari=k.id,
            status="IN PROGRESS"
        ).first()

        data.append({
            "id": str(k.id),
            "name": k.username,
            "phone": k.phone_no,
            "area": k.area,
            "status": k.status,
            "current_complaint": {
                "complaint_no": complaint.complaint_no
            } if complaint else None
        })

    return Response(data)
