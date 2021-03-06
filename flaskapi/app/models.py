from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(20), nullable=False)
    user_identity = db.Column(db.Integer, nullable=False) #user id
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def json_response(self):
        return {
            "token_id": self.id,
            "jti": self.jti,
            "token_type": self.token_type,
            "user_identity": self.user_identity,
            "revoked": self.revoked,
            "expires": self.expires
        }

    def __repr__(self):
        return '<Token {0}, {1}>'.format(self.id, ('revoked' if self.revoked else 'active'))


student_course = db.Table('user_course',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(100), nullable=False)
    last = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    isStudent = db.Column(db.Boolean, default=False, nullable=False)
    isTeacher = db.Column(db.Boolean, default=False, nullable=False)

    student = db.relationship('Student', uselist=False, backref='user')
    teacher = db.relationship('Teacher', uselist=False, backref='user')

    def full_name(self):
        return self.first + ' ' + self.last if self.first and self.last else None

    def create_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def token_response(self):
        data = self.json_response()
        data['user_details'].pop('password')
        return data

    def json_response(self):
        user = {
            "user_details": {
                "id": self.id,
                "name": self.full_name(),
                "email": self.email,
                "location": self.location,
                "password": self.password,
                "isStudent": self.isStudent,
                "isTeacher": self.isTeacher,
            }
        }

        if self.isStudent:
            user['student_details'] = {}
            courses_taking = self.student.courses_taking if self.student else None
            if courses_taking:
                user['student_details']['courses_taking'] = [
                    course.json_response(teacher=False) for course in courses_taking
                ]

        elif self.isTeacher:
            user['teacher_details'] = {}
            #If the teacher does not have any courses teaching yet, this protects against an error
            courses_teaching = self.teacher.courses_teaching if self.teacher else None
            if courses_teaching:
                user['teacher_details']['courses_teaching'] = [
                    course.json_response(teacher=True) for course in courses_teaching
                    ]

        return user

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #Additional fields for the 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    courses_taking = db.relationship('Course', secondary=student_course, lazy='subquery',
    backref=db.backref('students', lazy=True))

    def enroll_in_course(self, course_obj):
        self.courses_taking.append(course_obj)

    def json_response(self):
        return {
            "user_id": self.user_id,
            "name": self.user.full_name(),
            "courses_taking": [course.json_response() for course in self.courses_taking]
        }

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    github = db.Column(db.String(200), default=None, nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    link_to_resume = db.Column(db.String(200), default=None, nullable=True)
    approved = db.Column(db.Boolean, default=False)
    courses_teaching = db.relationship('Course', backref='teacher', lazy='dynamic')
    temp_password = db.Column(db.String(255), default=None)

    def json_response(self):
        return {
            "user_id": self.user_id,
            "name": self.user.full_name() if self.user else None
        }

    def check_temp_password(self, temp_password_recieved):
        if temp_password_recieved == self.temp_password:
            return True
        else:
            return False

    def __str__(self):
        return 'Teacher ' + str(self.user_id)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), default=None)
    description = db.Column(db.String(255), default=None)
    bio = db.Column(db.String(255), default=None)
    price = db.Column(db.Float, default=None)
    num_sales = db.Column(db.Integer, default=0)

    #Many courses have ONE teacher
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))

    #One course has many modules
    modules = db.relationship('Module', backref='course', lazy='dynamic')

    def json_response(self, teacher=False):
        course =  {
            "course_info": {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "bio": self.bio,
                "price": self.price,
                "numStudents": len(self.students),
                "teacher": self.teacher.json_response() if self.teacher else str(self.teacher)
            },
            "modules": [m.json_response() for m in self.modules]
        }

        if teacher:
            #If we are calling this function from the users route, exclude the teacher information.
            course['course_info'].pop('teacher')

        return course
    
class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), default=None)
    order = db.Column(db.Integer, default=None)
    info = db.Column(db.String(255), default=None)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def json_response(self):
        return {
            "name": self.name,
            "order": self.order,
            "info": self.info
        }