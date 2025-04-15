from flask import Flask, request, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from config import Config


app = Flask(__name__)
app.config.from_object(Config)



db = mysql.connector.connect(
    user=app.config['DB_USER'],
    password=app.config['DB_PASSWORD'],
    host=app.config['DB_HOST'],
    database=app.config['DB_NAME']
)

# Register a user


@app.route('/register_user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        role = data.get('role').lower()
        password = generate_password_hash(data.get('password'))

        if role not in ['student', 'lecturer', 'admin']:
            return make_response(jsonify({'error': 'invalid role'}), 400)

        cursor = db.cursor()

        # Insert into user table
        cursor.execute("""
            INSERT INTO User (firstName, lastName, role, password)
            VALUES (%s, %s, %s, %s)
        """, (firstName, lastName, role, password))

        # Get id of last user entered
        user_id = cursor.lastrowid

        if role == 'student':
            dob = data.get("dateOfBirth")
            if not dob:
                return make_response(jsonify({'error': 'Date of Birth is required for Student'}), 400)
            cursor.execute(
                "INSERT INTO Student (studentId,dateOfBirth) VALUES (%s,%s)", (user_id, dob))
        elif role == 'lecturer':
            department = data.get("department")
            if not department:
                return make_response(jsonify({'error': 'Department is required for Lecturer'}), 400)
            cursor.execute(
                "INSERT INTO Lecturer (lecturerId,department) VALUES (%s,%s)", (user_id, department))
        elif role == 'admin':
            cursor.execute(
                "INSERT INTO Admin  (adminId) VALUES (%s)", (user_id,))
        db.commit()
        return make_response(jsonify({'message': f"{role} added successfully, user ID is {user_id}"}), 201)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()

# Login by a user


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    userID = data.get('userId')
    password = data.get('password')
    cursor = db.cursor(dictionary=True)
    try:

        cursor.execute("SELECT * FROM User WHERE userId = %s", (userID,))
        user = cursor.fetchone()
        if user is None:
            return make_response(jsonify({'error': 'user does not exist'}), 400)

        # Compare password with the stored hashed password
        if check_password_hash(user['password'], password):
            return make_response(jsonify({'message': 'Login successful'}), 200)
        else:
            return make_response(jsonify({'error': 'Incorrect password'}), 401)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()


# Create a course by Admin
@app.route('/create_course', methods=['POST'])
def newCourse():
    data = request.get_json()
    courseId = data["courseId"]
    courseTitle = data["courseTitle"]
    adminId = data["adminId"]
    try:
        cursor = db.cursor()

        # Check if the adminID exists in the admin table
        cursor.execute("SELECT * FROM Admin WHERE adminId = %s", (adminId,))
        admin = cursor.fetchone()
        if not admin:
            return make_response(jsonify({'error': 'Unauthorized. Only admins can create a course.'}), 403)

        cursor.execute("""
            INSERT INTO Course (courseId, courseTitle)
            VALUES (%s, %s)
        """, (courseId, courseTitle))

        cursor.execute("""
            INSERT INTO Creates (adminId, courseId)
            VALUES (%s, %s)
        """, (adminId, courseId))

        db.commit()
        return make_response(jsonify({'message': f"Course {courseId} created successfully"}), 201)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()

# Get all courses on the system


@app.route('/get_courses', methods=['GET'])
def get_all_courses():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT courseId, courseTitle FROM Course")
        courselist = cursor.fetchall()
        return make_response(jsonify(courselist), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()

# Get courses by Student ID


@app.route('/get_course_student/<int:id>', methods=['GET'])
def get_student_courses(id):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT c.courseId, c.courseTitle
                      FROM Enrols e
                      JOIN Course c ON e.courseId = c.courseId
                      WHERE e.studentId = %s""", (id,))
        courselist = cursor.fetchall()
        return make_response(jsonify(courselist), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()

# Get courses by Lecturer ID


@app.route('/get_course_lecturer/<int:id>', methods=['GET'])
def get_lecturer_courses(id):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT c.courseId, c.courseTitle
                         FROM Teaches t
                      JOIN Course c ON c.courseId = t.courseId
                      WHERE t.lecturerId = %s
                      """, (id,))
        courselist = cursor.fetchall()
        return make_response(jsonify(courselist), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)
    finally:
        cursor.close()

# Register a Student for a course


@app.route('/register_course_student', methods=['POST'])
def register():
    data = request.get_json()
    studentId = data['studentId']  # get from session in frontend
    courseId = data['courseId']
    try:
        cursor = db.cursor()

        # Check if course exists
        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        course = cursor.fetchone()
        if not course:
            return make_response(jsonify({'error': 'Course not found'}), 404)

        # Check if student exists
        cursor.execute(
            "SELECT * FROM Student WHERE studentId = %s", (studentId,))
        student = cursor.fetchone()
        if not student:
            return make_response(jsonify({'error': 'Student not found'}), 404)

        # Check if already enrolled
        cursor.execute("""
            SELECT * FROM Enrols WHERE studentId = %s AND courseId = %s
        """, (studentId, courseId))
        if cursor.fetchone():
            return make_response(jsonify({'error': 'Student already enrolled in this course'}), 400)

        # Check if student does max of 6 course
        cursor.execute(""" SELECT COUNT(studentId)
                           FROM Enrols
                           WHERE studentId = %s""", (studentId,))

        count = cursor.fetchone()[0]
        if count >= 6:
            return make_response(jsonify({'error': 'Student already does 6 courses.'}), 400)
        else:
            # Register student for course
            cursor.execute("""
                INSERT INTO Enrols (studentId, courseId)
                VALUES (%s, %s)
            """, (studentId, courseId))
            db.commit()

        return make_response(jsonify({'message': f"Student {studentId} registered successfully for {courseId}"}), 201)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)

    finally:
        cursor.close()

# Assign a Lecturer to teach a course


@app.route('/register_course_lecturer', methods=['POST'])
def teach():
    data = request.get_json()
    lecturerId = data['lecturerId']  # get from session in frontend
    courseId = data['courseId']
    try:
        cursor = db.cursor()

        # Check if course exists
        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        course = cursor.fetchone()
        if not course:
            return make_response(jsonify({'error': 'Course not found'}), 404)

        # Check if lecturer exists
        cursor.execute(
            "SELECT * FROM Lecturer WHERE lecturerId = %s", (lecturerId,))
        lecturer = cursor.fetchone()
        if not lecturer:
            return make_response(jsonify({'error': 'Lecturer not found'}), 404)

        # Check if already teaches
        cursor.execute("""
            SELECT * FROM Teaches WHERE lecturerId = %s AND courseId = %s
        """, (lecturerId, courseId))
        if cursor.fetchone():
            return make_response(jsonify({'error': 'Lecturer already teaches in this course'}), 400)

        # Check if lecturer teaches max of 5 course
        cursor.execute(""" SELECT COUNT(lecturerId)
                           FROM Teaches
                           WHERE lecturerId = %s""", (lecturerId,))

        count = cursor.fetchone()[0]
        if count >= 5:
            return make_response(jsonify({'error': 'Lecturer already teaches 5 courses.'}), 400)
        else:
            # Check if course already has a lecturer
            cursor.execute(
                """SELECT lecturerId FROM Teaches WHERE courseId = %s""", (courseId,))
            lecturer = cursor.fetchone()

            if lecturer:
                # Reassign lecturer for course
                cursor.execute("""
                    UPDATE Teaches
                    SET lecturerId = %s
                    WHERE courseId = %s
                """, (lecturerId, courseId))
            else:
                # Register lecturer for course
                cursor.execute("""
                    INSERT INTO Teaches (lecturerId, courseId)
                    VALUES (%s, %s)
                """, (lecturerId, courseId))

            db.commit()

        return make_response(jsonify({'message': f"Lecturer {lecturerId} assigned successfully to course {courseId}"}), 201)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 500)

    finally:
        cursor.close()

# Get members of a particular course


@app.route('/course/members/<courseId>', methods=['GET'])
def getCourseMembers(courseId):
    try:
        cursor = db.cursor(dictionary=True)

        # Check if course exists
        cursor.execute(
            """SELECT * FROM Course WHERE courseId = %s""", (courseId,))
        course = cursor.fetchone()
        if not course:
            return make_response(jsonify({'error': 'Course not found'}), 404)

        # Get lecturer for course
        cursor.execute("""
            SELECT u.userId, u.firstName, u.lastName, u.role
            FROM Teaches t
            JOIN Lecturer l ON t.lecturerId = l.lecturerId
            JOIN Users u ON u.userId = l.lecturerId
            WHERE t.courseId = % s
            LIMIT 1;
        """, (courseId,))
        lecturer = cursor.fetchone()
        members = []
        if lecturer:
            for userId, firstName, lastName, role in lecturer:
                members.append({
                    "userId": userId,
                    "firstName": firstName,
                    "lastName": lastName,
                    "role": role
                })
        # Get students for course
        cursor.execute("""
            SELECT u.userId, u.firstName, u.lastName, u.role
            FROM Enrols e
            JOIN Student s ON e.studentId =s.studentId
            JOIN Users u ON u.userId = s.studentId
            WHERE e.courseId=%s;
        """, (courseId,))
        students = cursor.fetchall()
        for userId, firstName, lastName, role in students:
            members.append({
                "userId": userId,
                "firstName": firstName,
                "lastName": lastName,
                "role": role
            })
        return make_response(jsonify(members), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()  

# Should be able to retrieve all calendar events for a particular course


@app.route('/events/<courseId>', methods=['GET'])
def getCalendarEventsByCourse(courseId):
    try:

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM Calendar_Events WHERE courseId =%s;', (courseId,))
        events = cursor.fetchall()
        return make_response(jsonify(events), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()


# Get calandar events for a particular student on a particular date
@app.route('/Calendar_Events/<studentId>/<Date>', methods=['GET'])
def getEventsStudent(studentId, Date):
    try:
        cursor = db.cursor(dictionary=True)
        # Check if student exists
        cursor.execute(
            "SELECT * FROM Student WHERE studentId = %s", (studentId,))
     
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Student not found'}), 404)

        cursor.execute("""
            SELECT cal.eventTitle, cal.beginning, cal.end, c.courseId, c.courseTitle
            FROM Calendar_Events cal
            JOIN Course c ON cal.courseId=c.courseId
            JOIN Enrols e ON cal.courseId=e.courseId
            WHERE e.studentId=% s AND (cal.beginning = % s OR cal.end = % s)
            ORDER BY cal.beginning ASC;
        """, (studentId, Date, Date))
        events = cursor.fetchall()
        if not events:
            return make_response(jsonify({'error': 'No events found'}), 404)
        return make_response(jsonify(events), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# Add a calendar event for a course


@app.route('/add/calendarEvent', methods=['POST'])
def addCalendarEvent():
    try:

        data = request.get_json()
        eventTitle = data['eventTitle']
        beginning = data['beginning']
        end = data['end']
        courseId = data['courseId']

        cursor = db.cursor()

        
        cursor.execute("SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)


        cursor.execute("""SELECT 1 FROM Calendar_Events WHERE eventTitle = %s AND courseId = %s
        """, (eventTitle, courseId))

        if cursor.fetchone():
            return jsonify({'error': "An event with the title already exists for this course"}), 400
        cursor.execute(
            "INSERT INTO Calendar_Events (eventTitle,courseId,beginning,end) VALUES (%s, %s, %s, %s);", (eventTitle, courseId, beginning, end))

        db.commit()
        return make_response(jsonify({'message': "Event added"}), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# Get all discussion forums for a course


@app.route('/forums/<courseId>', methods=['GET'])
def getForums(courseId):
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)

        cursor.execute(
            "SELECT * FROM Discussion_Forum WHERE courseId = %s;", (courseId,))

        forums = cursor.fetchall()
        return make_response(jsonify(forums), 200)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# Add a discussion forum for a course


@app.route('/add/forum', methods=['POST'])
def addForum():
    try:
        cursor = db.cursor()

        data = request.get_json()
        courseId = data['courseId']
        forumTitle = data['forumTitle']

        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)
        cursor.execute("""
            INSERT INTO Discussion_Forum(courseId, forumTitle)
            VALUES (%s, %s)
        """, (courseId, forumTitle))
        db.commit()
        return make_response(jsonify({'message': "Forum added"}), 200)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

@app.route('/get/threads/<int:courseId>/<string:forumTitle>', methods=['GET'])
def getThreads(courseId, forumTitle):
    try:
        cursor = db.cursor(dictionary=True)

       
        cursor.execute("SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)
        
        cursor.execute(
            "SELECT forumId FROM Discussion_Forum WHERE courseId = %s AND forumTitle = %s",
            (courseId, forumTitle)
        )
        forum = cursor.fetchone()
        if not forum:
            return make_response(jsonify({'error': 'Forum not found'}), 404)
        forumId = forum['forumId']

        cursor.execute(
            "SELECT threadId, userId, content, datePosted FROM Discussion_Thread WHERE forumId = %s",
            (forumId,)
        )
        threads = cursor.fetchall()

        allThreads = []
        for thread in threads:
            threadId = thread['threadId']


            cursor.execute(
                "SELECT postId, userId, content, datePosted, parentPostId FROM Posts WHERE threadId = %s",
                (threadId,)
            )
            posts = cursor.fetchall()

            postDict = {post['postId']: {**post, 'replies': []} for post in posts}
            replies = []

            for post in posts:
                if post['parentPostId'] is None:
                    replies.append(postDict[post['postId']])
                else:
                    parent = postDict.get(post['parentPostId'])
                    if parent:
                        parent['replies'].append(postDict[post['postId']])

            
            threadData = {
                'threadId': thread['threadId'],
                'userId': thread['userId'],
                'content': thread['content'],
                'datePosted': thread['datePosted'],
                'replies': replies
            }

            allThreads.append(threadData)

        return jsonify({'threads': allThreads})

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)


#Add discussion thread to discussion forum
@app.route('/add/discussionThread',methods=['POST'])
def addThread():
    try:
            cursor = db.cursor()
            data = request.get_json()
            forumId = data["forumId"]
            title = data["title"]
            userId = data["userId"]
            content = data["content"]
    
   
            cursor.execute("SELECT * FROM Discussion_Forum WHERE formId = %s", (forumId,))
            if not cursor.fetchone():
                return make_response(jsonify({'error': 'Forum not found'}), 404)

            cursor.execute("SELECT * FROM User WHERE userId = %s", (userId,))
            if not cursor.fetchone():
                return make_response(jsonify({'error': 'User not found'}), 404)

            
            cursor.execute("""
                INSERT INTO Discussion_Thread (forumId, userId, content, title, datePosted)
                VALUES (%s, %s, %s, %s, NOW())
            """, (forumId, userId, content, title))

           
            db.commit()

            return make_response(jsonify({'message': 'Thread added successfully'}), 201)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

#Reply to threads
@app.route('/reply/thread', methods=['POST'])
def replyToThread():
    try:
        cursor = db.cursor()
        data = request.get_json()

        threadId = data.get("threadId")
        userId = data.get("userId")
        content = data.get("content")

      
        cursor.execute("SELECT * FROM Discussion_Thread WHERE threadId = %s", (threadId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Thread not found'}), 404)

        cursor.execute("SELECT * FROM User WHERE userId = %s", (userId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'User not found'}), 404)

        cursor.execute("""
            INSERT INTO Posts (threadId,forumId,userId, content,datePosted, parentPostId)
            VALUES (%s,%s,%s, NOW(), NULL)
        """, (threadId,userId,content))

        db.commit()
        return make_response(jsonify({'message': 'Reply to thread added successfully'}), 201)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

#Reply to replies
@app.route('/reply/replies',methods=['POST'])
def replyToReplies():

    try:
        cursor = db.cursor()
        data = request.get_json()

        threadId = data.get("threadId")
        userId = data.get("userId")
        content = data.get("content")
        parentPostId = data.get("parentPostId")

        cursor.execute("SELECT * FROM Discussion_Thread WHERE threadId = %s", (threadId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Thread not found'}), 404)

        cursor.execute("SELECT * FROM User WHERE userId = %s", (userId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'User not found'}), 404)

        cursor.execute("SELECT * FROM Posts WHERE postId = %s", (parentPostId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Parent post not found'}), 404)

        cursor.execute("""
            INSERT INTO Posts (threadId, userId, content, parentPostId, datePosted)
            VALUES (%s, %s, %s, %s, NOW())
        """, (threadId, userId, content, parentPostId))

        db.commit()
        return make_response(jsonify({'message': 'Reply to reply added successfully'}), 201)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()




# A lecturer should have the ability to add course content
@app.route('/add/content', methods=['POST'])
def addContent():
    try:

        cursor = db.cursor()
        data = request.get_json()
        courseId = data["courseId"]
        sectionTitle = data["sectionTitle"]

        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)

        cursor.execute(
            "INSERT INTO Section (courseId, sectionTitle) VALUES (%s, %s);", (courseId, sectionTitle))

        link = data["Link"]
        file = data["File"]
        slide = data["Slide"]
        sectionId = cursor.lastrowid
        cursor.execute("""
            INSERT INTO Content(sectionId, link, file, slide)
            VALUES ( %s, %s, %s, %s)
            """, (sectionId, link, file, slide))

        db.commit()
        return make_response(jsonify({'message': 'content added'}), 200)

    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()


# Should be able to retrieve all the course content for a particular course


@app.route('/content/<courseId>', methods=['GET'])
def getCourseContent(courseId):
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM Course WHERE courseId = %s", (courseId,))
        if not cursor.fetchone():
            return make_response(jsonify({'error': 'Course not found'}), 404)

        cursor.execute("""
                    SELECT
                        section.sectionTitle,
                        content.link,
                        content.file,
                        content.slide
                    FROM
                        Content content
                    JOIN
                        Section section ON section.sectionId=content.sectionId
                    WHERE
                        section.courseId=%s;
                """, (courseId,))
        content = cursor.fetchall()
        return make_response(jsonify(content), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()


#Student can submit assignment

@app.route("/submitAssignment",methods=['POST'])

def submitAssign():
     try:
        data = request.get_json()
        assignmentId = data.get('assignmentId')
        studentId = data.get('studentId')
        submissionFile = data.get('submissionFile')
        
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Assignment WHERE assignmentId = %s", (assignmentId,))
        if not cursor.fetchone():
            return jsonify({'error': 'Assignment not found'}), 404

        cursor.execute("SELECT * FROM Student WHERE studentId = %s", (studentId,))
        if not cursor.fetchone():
            return jsonify({'error': 'Student not found'}), 404

        cursor.execute("SELECT * FROM Submits WHERE studentId = %s AND assignmentId = %s", (studentId, assignmentId))
        if cursor.fetchone():
            return jsonify({'error': 'You already submitted this assignment'}), 409
        
        cursor.execute("""INSERT INTO Submits (studentId, assignmentId, assignmentGrade, submissionTime, submissionFile)
            VALUES (%s, %s,%s,NOW(),%s)""", (studentId,assignmentId,None,submissionFile))
            
        db.commit()
        db.close()

        return jsonify({'message': 'Assignment submitted'}), 201
     except Exception as e:
        return jsonify({'error': str(e)}), 500

     finally:
        cursor.close()

#lecturer can grade an assignment
@app.route("/submit/assigment/grade", methods=['PUT'])
def submitGrade():
    try:
            data = request.get_json()
            assignmentId = data.get('assignmentId')
            studentId = data.get('studentId')
            assignmentGrade = data.get('grade')

            cursor = db.cursor()
            
            cursor.execute("SELECT * FROM Assignment WHERE assignmentId = %s", (assignmentId,))
            if not cursor.fetchone():
               return jsonify({'error': 'Assignment not found'}), 404

            cursor.execute("SELECT * FROM Student WHERE studentId = %s", (studentId,))
            if not cursor.fetchone():
               return jsonify({'error': 'Student not found'}), 404

            cursor.execute("""UPDATE Submits SET assignmentgrade = %s
                    WHERE assignmentId = %s AND studentId = %s
                """,(assignmentGrade,assignmentId,studentId))
            db.commit()
            

            return jsonify({'message': 'Grade added successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        db.close()

#Get Average
@app.route("/get/studentAverage", methods=['GET'])
def getStudentAverage():
    try:
        data = request.get_json()
        studentId = data.get('studentId')
        courseId= data.get('courseId')

        cursor = db.cursor()

        cursor.execute("""
            SELECT assign.assignmentId, submit.assignmentGrade
            FROM assignment assign
            JOIN submits submit ON assign.assignmentId = submit.assignmentId
            WHERE assign.courseId = %s AND submit.studentId = %s AND submit.assignmentGrade IS NOT NULL
        """,(courseId,studentId))
    
        
        getSubmitted = cursor.fetchall()

        if not getSubmitted:
            return jsonify({'message': 'No graded assignments found'}), 404
        
        total = sum([getSubmitted[1] for i in getSubmitted])
        avg = total / len(getSubmitted)

        return jsonify({
            'studentId': studentId,
            'courseId': courseId,
            'overallAvg': round(avg, 2)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        db.close()
#Add assignment
@app.route('/addAssigment',methods=['POST'])
def addAssignment():
   try:
        data = request.get_json()
        courseId =data.get('courseId')
        assignmentTitle = data.get('assignmentTitle')

        cursor = db.cursor()
        cursor.execute("INSERT INTO Assignment (courseId, assignmentTitle) VALUES (%s,%s)", 
                       (courseId, assignmentTitle))
        db.commit()

        return jsonify({'message': 'Assignment added successfully'}), 200
   except Exception as e:
        return jsonify({'error': str(e)}), 500

   finally:
        cursor.close()
        db.close()

# Get courses with over 50 or more students


@app.route('/report/courses50', methods=['GET'])
def get_courses_50plus():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM courses_50_over""")
        courses = cursor.fetchall()
        return make_response(jsonify(courses), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()


# Get students in 5 or more courses
@app.route('/report/students/courses5', methods=['GET'])
def getStudentsFiveCourse():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM student_course_5_over""")
        courses = cursor.fetchall()
        return make_response(jsonify(courses), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# Get lecturers that teach three or more courses


@app.route('/report/lecturers/courses3', methods=['GET'])
def getLecturersCourses3():
    try:

        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM lecturer_teach_3_over""")
        lecturers = cursor.fetchall()
        return make_response(jsonify(lecturers), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# Get the top ten most enrolled courses


@app.route('/report/courses/top10', methods=['GET'])
def getCourseTop10():
    try:

        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM top10courses""")
        courses = cursor.fetchall()
        return make_response(jsonify(courses), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()

# The top 10 students with the highest overall averages.


@app.route('/report/students/top10', methods=['GET'])
def getStudentsTop10():
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT * FROM top10students""")
        students = cursor.fetchall()
        return make_response(jsonify(students), 200)
    except Error as e:
        return make_response(jsonify({'error': str(e)}), 400)
    finally:
        cursor.close()


if __name__ == '__main__':
    app.run(port=6000)
