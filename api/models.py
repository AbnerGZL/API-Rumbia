from django.db import models
from django.utils import timezone

# -----------------------------------------------------
# USERS
# -----------------------------------------------------
class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    user_code = models.CharField(max_length=45)
    email = models.EmailField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=250)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    phone = models.CharField(max_length=45, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        db_table = 'user'


# -----------------------------------------------------
# TOKENS
# -----------------------------------------------------
class RefreshTokenModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    jti = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() >= self.expires_at

# -----------------------------------------------------
# CAREERS CATEGORIES
# -----------------------------------------------------
class CareerCategories(models.Model):
    id_category = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name
    
    class Meta:
        db_table = 'career_category'


# -----------------------------------------------------
# CAREERS
# -----------------------------------------------------
class Career(models.Model):
    id_career = models.AutoField(primary_key=True)
    category = models.ForeignKey(CareerCategories, on_delete=models.CASCADE)
    name_career = models.CharField(max_length=80)
    desc_career = models.TextField(max_length=250)
    duration_years = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_career
    
    class Meta:
        db_table = 'career'


# -----------------------------------------------------
# LEARNERS
# -----------------------------------------------------
class Learner(models.Model):
    id_learner = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    educational_level = models.CharField(max_length=45, null=True, blank=True)
    current_grade = models.CharField(max_length=20, null=True, blank=True)
    interests = models.TextField(max_length=100, null=True, blank=True)
    career_interests = models.TextField(max_length=100, null=True, blank=True)
    prefered_schedule = models.CharField(max_length=20, null=True, blank=True)
    is_learner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Learner: {self.user.first_name}"
    
    class Meta:
        db_table = 'learner'    


# -----------------------------------------------------
# MENTOR
# -----------------------------------------------------
class Mentor(models.Model):
    id_mentor = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    career = models.ForeignKey(Career, on_delete=models.SET_NULL,null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2,default=0.0)
    total_sessions = models.IntegerField(default=0)
    is_mentor = models.BooleanField(default=False)
    # profile_img = models.TextField(max_length=100, null=True, blank=True)
    profile_img = models.ImageField(upload_to='mentors/', null=True, blank=True)
    description = models.TextField(max_length=350, null=False, blank=False)
    alt_career = models.TextField(max_length=60,null=True, blank=True)
    language = models.TextField(max_length=45, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mentor: {self.user.first_name}"
    
    class Meta:
        db_table = 'mentor'

# -----------------------------------------------------
# SESSIONS
# -----------------------------------------------------
class Session(models.Model):
    id_session = models.AutoField(primary_key=True)
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=80, unique=True)
    schedule_date = models.DateTimeField()
    duration_minutes = models.IntegerField(null=True, blank=True)
    session_status = models.CharField(max_length=50)
    meeting_url = models.TextField(max_length=500, null=True, blank=True)
    meeting_platform = models.CharField(max_length=45)
    session_notes = models.TextField(max_length=250)
    student_feedback = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    topic = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    recording_url = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.uuid} - {self.mentor}"
    
    class Meta:
        db_table = 'session'


# -----------------------------------------------------
# PAYMENTS
# -----------------------------------------------------
class Payment(models.Model):
    id_pay = models.AutoField(primary_key=True)
    data_session = models.OneToOneField('DataSession', on_delete=models.CASCADE)
    is_trial = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(max_length=45, null=True, blank=True)
    payment_status = models.CharField(max_length=45)
    payment_method = models.CharField(max_length=45, null=True, blank=True)
    transaction_id = models.CharField(max_length=255)
    receipt_img = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id_pay} - {self.payment_status}"
    
    class Meta:
        db_table = 'payment'


# -----------------------------------------------------
# DATA_SESSIONS
# -----------------------------------------------------
class DataSession(models.Model):
    id_data = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_present = models.BooleanField(null=True, blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DataSession for {self.user.first_name} in session {self.session.uuid}"
    
    class Meta:
        db_table = 'data_session'    


# -----------------------------------------------------
# REVIEWS
# -----------------------------------------------------
class Review(models.Model):
    id_review = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review {self.id_review} by {self.user.first_name}"

    class Meta:
        db_table = 'review'


# -----------------------------------------------------
# PROFESSIONAL_PROFILE
# -----------------------------------------------------
class ProfessionalProfile(models.Model):
    id_professional = models.AutoField(primary_key=True)
    mentor = models.OneToOneField(Mentor, on_delete=models.CASCADE)
    pro_title = models.CharField(max_length=60)
    experience_years = models.IntegerField(default=0)
    college = models.CharField(max_length=55, null=True, blank=True)
    is_certified = models.BooleanField(default=False)
    cv_url = models.TextField(max_length=100, null=True, blank=True)
    graduation_year = models.DateField()
    work_experience = models.JSONField(null=True, blank=True)
    skills = models.TextField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pro_title} - {self.mentor}"
    
    class Meta:
        db_table = 'professional_profile'    


# -----------------------------------------------------
# STUDENT_PROFILE
# -----------------------------------------------------
class StudentProfile(models.Model):
    id_student = models.AutoField(primary_key=True)
    mentor = models.OneToOneField(Mentor, on_delete=models.CASCADE)
    college = models.CharField(max_length=60)
    current_semester = models.IntegerField()
    work_experience = models.JSONField(null=True, blank=True)
    skills = models.TextField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StudentProfile {self.id_student} - {self.institution_name}"
    
    class Meta:
        db_table = 'student_profile'