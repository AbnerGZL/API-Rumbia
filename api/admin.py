from django.contrib import admin
from .models import (
    User, RefreshTokenModel, CareerCategories, Career,
    Learner, Mentor, Session, Payment, DataSession,
    Review, ProfessionalProfile, StudentProfile
)

# -------------------------
# USER
# -------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id_user", "first_name", "last_name", "email", "is_active", "is_verified", "last_login")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_active", "is_verified")


# -------------------------
# TOKENS
# -------------------------
@admin.register(RefreshTokenModel)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "jti", "created_at", "expires_at", "revoked")
    search_fields = ("jti",)
    list_filter = ("revoked",)


# -------------------------
# CAREER CATEGORIES
# -------------------------
@admin.register(CareerCategories)
class CareerCategoriesAdmin(admin.ModelAdmin):
    list_display = ("id_category", "category_name", "created_at")
    search_fields = ("category_name",)


# -------------------------
# CAREER
# -------------------------
@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ("id_career", "name_career", "category", "duration_years", "created_at")
    list_filter = ("category",)
    search_fields = ("name_career",)


# -------------------------
# LEARNER
# -------------------------
@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ("id_learner", "user", "educational_level", "current_grade", "is_learner", "created_at")
    list_filter = ("is_learner",)
    search_fields = ("user__first_name", "user__last_name")


# -------------------------
# MENTOR
# -------------------------
@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ("id_mentor", "user", "career", "rating", "total_sessions", "is_mentor")
    search_fields = ("user__first_name", "user__last_name")
    list_filter = ("is_mentor", "career")


# -------------------------
# SESSION
# -------------------------
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id_session", "mentor", "uuid", "schedule_date", "session_status", "price")
    list_filter = ("session_status", "schedule_date")
    search_fields = ("uuid",)


# -------------------------
# PAYMENT
# -------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id_pay", "amount", "currency", "payment_status", "payment_method", "transaction_id")
    search_fields = ("transaction_id", "payment_status")


# -------------------------
# DATA SESSION
# -------------------------
@admin.register(DataSession)
class DataSessionAdmin(admin.ModelAdmin):
    list_display = ("id_data", "session", "user", "payment", "is_present", "created_at")
    list_filter = ("is_present",)


# -------------------------
# REVIEW
# -------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id_review", "session", "user", "score", "created_at")
    list_filter = ("score",)
    search_fields = ("user__first_name", "user__last_name")


# -------------------------
# PROFESSIONAL PROFILE
# -------------------------
@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ("id_professional", "mentor", "pro_title", "experience_years", "is_certified")


# -------------------------
# STUDENT PROFILE
# -------------------------
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("id_student", "mentor", "college", "current_semester")
