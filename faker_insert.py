import random
from faker import Faker

fake = Faker()
random.seed(42)

numberofStudents = 100_000
numberofCourses = 200
minCoursePerStudent = 3
maxCoursePerStudent = 6
minStudentPerCourse = 10
maxStudentPerLecturer = 5

# Start user ID from 625000000
userIdStart = 625000000
courseIdStart = 1
lecturerIdStart = userIdStart + numberofStudents
adminIdStart = lecturerIdStart + 1000  

counter = userIdStart
courseId = [f"C{1000 + i}" for i in range(numberofCourses)]

# Students 
students = []
usersSql= []
studentsSql = []

for _ in range(numberofStudents):
    firstName = fake.first_name()
    lastName = fake.last_name()
    dateOfBirth = fake.date_of_birth(minimum_age=18, maximum_age=30)

    usersSql.append(
        f"INSERT INTO User (userId, firstName, lastName, role, password) VALUES "
        f"({counter}, '{firstName}', '{lastName}', 'student', 'password123');"
    )
    studentsSql.append(
        f"INSERT INTO Student (studentId, dateOfBirth) VALUES ({counter}, '{dateOfBirth}');"
    )
    students.append(counter)
    counter += 1

# Generate Courses 
coursesSql = []
for cid in courseId:
    coursesSql.append(
        f"INSERT INTO Course (courseId, courseTitle) VALUES ('{cid}', '{fake.catch_phrase()}');"
    )

#Generate Lecturers 
lecturers = []
lecturersSql = []
lecturerUsersSql = []

for i in range(67): 
    lid = lecturerIdStart + i
    firstName = fake.first_name()
    lastName = fake.last_name()
    department = fake.bs().split()[0].capitalize() + " Dept"

    lecturerUsersSql.append(
        f"INSERT INTO User (userId, firstName, lastName, role, password) VALUES "
        f"({lid}, '{firstName}', '{lastName}', 'lecturer', 'password123');"
    )
    lecturersSql.append(
        f"INSERT INTO Lecturer (lecturerId, Department) VALUES ({lid}, '{department}');"
    )
    lecturers.append(lid)

# Assign Lecturers to Courses
teachesSql = []
lecturerDict = {lect: [] for lect in lecturers}
coursesAvailable = courseId.copy()
random.shuffle(coursesAvailable)

# Step 1: Assign at least one course to each lecturer
for lect in lecturers:
    # Assign a random course to each lecturer
    if coursesAvailable:
        course = coursesAvailable.pop()
        teachesSql.append(
            f"INSERT INTO Teaches (lecturerId, courseId) VALUES ({lect}, '{course}');"
        )
        lecturerDict[lect].append(course)

# Step 2: Assign remaining courses to lecturers while respecting maxStudentPerLecturer
for cid in coursesAvailable:
    lectAvailable = [l for l, c in lecturerDict.items() if len(c) < maxStudentPerLecturer]
    lect = random.choice(lectAvailable)
    teachesSql.append(
        f"INSERT INTO Teaches (lecturerId, courseId) VALUES ({lect}, '{cid}');"
    )
    lecturerDict[lect].append(cid)

# Enroll Students
enrolsSql = []
courseDict = {cid: set() for cid in courseId}
studentCount = {sid: 0 for sid in students}

# Randomly assign each student 3 to 6 courses
for sid in students:
    numberofCourses = random.randint(
        minCoursePerStudent, maxCoursePerStudent)
    coursesAvailable = random.sample(courseId, len(courseId)) 
    assignedCourses = 0

    for cid in coursesAvailable:
        if assignedCourses >= numberofCourses:
            break
        enrolsSql.append(
            f"INSERT INTO Enrols (studentId, courseId, grade) VALUES ({sid}, '{cid}', {random.randint(0, 100)});"
        )
        courseDict[cid].add(sid)
        studentCount[sid] += 1
        assignedCourses += 1

#each course has at least 10 students
for cid, studentSet in courseDict.items():
    while len(studentSet) < minStudentPerCourse:
        sid = random.choice(students)
        if sid not in studentSet and studentCount[sid] < maxCoursePerStudent:
            enrolsSql.append(
                f"INSERT INTO Enrols (studentId, courseId, grade) VALUES ({sid}, '{cid}', {random.randint(0, 100)});"
            )
            courseDict[cid].add(sid)
            studentCount[sid] += 1


# Output  
with open("insertUsers.sql", "w") as f:
    f.write("\n".join(usersSql + lecturerUsersSql))

with open("insertStudents.sql", "w") as f:
    f.write("\n".join(studentsSql))

with open("insertLecturers.sql", "w") as f:
    f.write("\n".join(lecturersSql))

with open("insertCourses.sql", "w") as f:
    f.write("\n".join(coursesSql))

with open("insertTeaches.sql", "w") as f:
    f.write("\n".join(teachesSql))

with open("insertEnrols.sql", "w") as f:
    f.write("\n".join(enrolsSql))


# Generate Admins
numberOfAdmin = 50
admins = []
adminUsersSql = []
adminsSql = []

for i in range(numberOfAdmin):
    aid = adminIdStart + i
    firstName = fake.first_name()
    lastName = fake.last_name()

    adminUsersSql.append(
        f"INSERT INTO User (userId, firstName, lastName, role, password) VALUES "
        f"({aid}, '{firstName}', '{lastName}', 'admin', 'password123');"
    )
    adminsSql.append(f"INSERT INTO Admin (adminId) VALUES ({aid});")
    admins.append(aid)

# Creates (Admins Creating Courses)
createsSql = []
for cid in courseId:
    aid = random.choice(admins)
    createsSql.append(
        f"INSERT INTO Creates (adminId, courseId) VALUES ({aid}, '{cid}');"
    )

# Assignments per Course
assignmentsSql = []
assignmentId = 1
courseAssignments = {} 

for cid in courseId:
    numberOfAssignments = random.randint(2, 5)
    courseAssignments[cid] = []
    for _ in range(numberOfAssignments):
        title = fake.sentence(nb_words=5).replace("'", "''")
        assignmentsSql.append(
            f"INSERT INTO Assignment (courseId, assignmentTitle) "
            f"VALUES ('{cid}', '{title}');"
        )
        courseAssignments[cid].append(assignmentId)
        assignmentId += 1

# Students submitting assignments
submitsSql = []
for cid, studentsInCourse in courseDict.items():
    for aid in courseAssignments[cid]:
        for sid in random.sample(list(studentsInCourse), min(5, len(studentsInCourse))):
            grade = random.randint(40, 100)
            submissionTime = fake.date_between(
                start_date='-90d', end_date='today')
            submitsSql.append(
                f"INSERT INTO Submits (studentId, assignmentId, assignmentGrade, submissionTime, submissionFile) VALUES "
                f"({sid}, {aid}, {grade}, '{submissionTime}', 'submittedFile{aid}_{sid}.pdf');"
            )

# Events
eventsSql = []
eventId = 1
for cid in courseId:
    numberOfEvents = random.randint(1, 3)
    for _ in range(numberOfEvents):
        startDate = fake.date_between(start_date='-60d', end_date='+30d')
        endDate = fake.date_between(start_date=startDate, end_date='+30d')
        eventTitle = fake.catch_phrase().replace("'", "''")
        eventsSql.append(
            f"INSERT INTO Calendar_Events (courseId, beginning, end, eventTitle) "
            f"VALUES ('{cid}', '{startDate}', '{endDate}', '{eventTitle}');"
        )
        eventId += 1

#Output
with open("insertAdmins.sql", "w") as f:
    f.write("\n".join(adminUsersSql + adminsSql))

with open("insertCreates.sql", "w") as f:
    f.write("\n".join(createsSql))

with open("insertAssignments.sql", "w") as f:
    f.write("\n".join(assignmentsSql))

with open("insertSubmits.sql", "w") as f:
    f.write("\n".join(submitsSql))

with open("insertEvents.sql", "w") as f:
    f.write("\n".join(eventsSql))


# Discussion Forum
forumsSql = []
forumId = 1
courseForumMap = {}

for cid in courseId:
    forumTitle = f"{fake.bs().capitalize()} Forum"
    forumsSql.append(
        f"INSERT INTO Discussion_Forum (courseId, forumTitle) VALUES ('{cid}', '{forumTitle}');"
    )
    courseForumMap[cid] = forumId
    forumId += 1

# Discussion Threads 
threadsSql = []
threadId = 1

for cid in courseId:
    fid = courseForumMap[cid] 
    studentsInCourse = list(courseDict[cid])
    lecturersInCourse = [lid for lid, courses in lecturerDict.items() if cid in courses]

    validUsers = studentsInCourse + lecturersInCourse 
    numThreads = random.randint(2, 6)  

    for _ in range(numThreads):
        uid = random.choice(validUsers)  
        date = fake.date_between(start_date='-30d', end_date='today') 
        title = fake.sentence(nb_words=6).replace("'", "''") 
        initialPost = fake.paragraph(nb_sentences=2).replace("'", "''") 

        # Insert the thread into the database
        threadsSql.append(
            f"INSERT INTO Discussion_Thread (forumId, userId, datePosted, title, content) "
            f"VALUES ({fid}, {uid}, '{date}', '{title}', '{initialPost}');"
        )
        
        threadId += 1

# Generating Replies for Threads
postSql = []
postId = 1

for cid in courseId:
    fid = courseForumMap[cid]
    studentsInCourse = list(courseDict[cid])
    lecturersInCourse = [lid for lid, courses in lecturerDict.items() if cid in courses]

    validUsers = studentsInCourse + lecturersInCourse 
    numThreads = random.randint(2, 6)  

    for threadId in range(1, numThreads + 1):  
        # Generate replies for each thread
        numReplies = random.randint(1, 4)
        replyIds = []
        
        for _ in range(numReplies):
            replier = random.choice(validUsers)
            replyDate = fake.date_between(start_date='-30d', end_date='today')  
            replyContent = fake.sentence().replace("'", "''")  

            
            parentReplyId = random.choice(replyIds) if replyIds and random.random() > 0.5 else "NULL"

            # Insert the reply into the Posts table
            postSql.append(
                f"INSERT INTO Posts (threadId, userId, content, datePosted, parentPostId) "
                f"VALUES ({threadId}, {replier}, '{replyContent}', '{replyDate}', {parentReplyId});"
            )
            
            replyIds.append(postId)
            postId += 1

# Output
with open("insert_replies.sql", "w") as f:
    f.write("\n".join(postSql))


# Section per Course 
sectionSql = []
sectionId = 1
courseSection = {}

for cid in courseId:
    numSection = random.randint(2, 4)
    sectionIds = []
    for _ in range(numSection):
        title = fake.catch_phrase().replace("'", "''")
        sectionSql.append(
            f"INSERT INTO Section (courseId, sectionTitle) VALUES ('{cid}', '{title}');"
        )
        sectionIds.append(sectionId)
        sectionId += 1
    courseSection[cid] = sectionIds

# Content per Section
contentsSql = []
contentId = 1

for sectionlist in courseSection.values():
    for tid in sectionlist:
        num_content = random.randint(1, 3)
        for _ in range(num_content):
            link = fake.url()
            file = f"lecture_{contentId}.pdf"
            slide = f"slide_{contentId}.pptx"
            contentsSql.append(
                f"INSERT INTO Content (sectionId, link, file, slide) VALUES "
                f"({tid}, '{link}', '{file}', '{slide}');"
            )
            contentId += 1

# Output
with open("insertForums.sql", "w") as f:
    f.write("\n".join(forumsSql))

with open("inserThreads.sql", "w") as f:
    f.write("\n".join(threadsSql))

with open("insertSections.sql", "w") as f:
    f.write("\n".join(sectionSql))

with open("insertContents.sql", "w") as f:
    f.write("\n".join(contentsSql))
