from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password


class LearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learner
        fields = '__all__'
        
class MentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = '__all__'
        
class UserSerializer(serializers.ModelSerializer):
    learner = LearnerSerializer(read_only=True)
    mentor = MentorSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['user_code', 'first_name', 'last_name', 'email', 'learner', 'mentor']
        

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    # def create(self, validated_data):
    #     # Encriptar el password antes de guardar
    #     if 'password_hash' in validated_data:
    #         validated_data['password_hash'] = make_password(validated_data['password_hash'])
    #     return super(USERSSerializer, self).create(validated_data)          

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerCategories
        fields = '__all__'

class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    mentor = MentorSerializer(read_only=True)
    career = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    class Meta:
        model = Session
        fields = '__all__'
        
    def get_career(self, obj):
        if obj.mentor and obj.mentor.career:
            return CareerSerializer(obj.mentor.career).data
        return None

    def get_category(self, obj):
        if obj.mentor and obj.mentor.career and obj.mentor.career.category:
            return CategoriesSerializer(obj.mentor.career.category).data
        return None
        
        
class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class Data_SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSession
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class Professional_ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfile
        fields = '__all__'


class Student_ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'
