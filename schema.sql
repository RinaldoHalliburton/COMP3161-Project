
DROP DATABASE IF EXISTS vle;
CREATE DATABASE vle;
USE vle;

-- Tables --

CREATE TABLE User (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    firstName VARCHAR(30) NOT NULL,
    lastName VARCHAR(30) NOT NULL,
    role VARCHAR(10) NOT NULL,
    password VARCHAR(200) NOT NULL
);

ALTER TABLE User AUTO_INCREMENT = 625000000;

CREATE TABLE Admin (
    adminId INT PRIMARY KEY,
    FOREIGN KEY (adminId) REFERENCES User(userId) ON DELETE CASCADE
);

CREATE TABLE Lecturer (
    lecturerId INT PRIMARY KEY,
    department VARCHAR(30) NOT NULL,
    FOREIGN KEY (lecturerId) REFERENCES User(userId) ON DELETE CASCADE
);

CREATE TABLE Student (
    studentId INT PRIMARY KEY,
    dateOfBirth DATE NOT NULL,
    FOREIGN KEY (studentId) REFERENCES User(userId) ON DELETE CASCADE
);


CREATE TABLE Course (
    courseId VARCHAR(255) PRIMARY KEY,
    courseTitle VARCHAR(255) NOT NULL
);

CREATE TABLE Teaches (
    lecturerId INT,
    courseId VARCHAR(255),
    PRIMARY KEY (lecturerId, courseId),
    FOREIGN KEY (lecturerId) REFERENCES Lecturer(lecturerId),
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Assignment (
    assignmentId INT AUTO_INCREMENT PRIMARY KEY,
    courseId VARCHAR(255),
    assignmentTitle VARCHAR(255) NOT NULL,
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Enrols (
    studentId INT,
    courseId VARCHAR(255),
    grade INT DEFAULT (0),
    PRIMARY KEY (studentId, courseId),
    FOREIGN KEY (studentId) REFERENCES Student(studentId),
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Submits (
    studentId INT,
    assignmentId INT,
    assignmentGrade INT DEFAULT NULL,
    submissionTime DATE,
    submissionFile VARCHAR(255),
    PRIMARY KEY (studentId, assignmentId),
    FOREIGN KEY (studentId) REFERENCES Student(studentId)
);

CREATE TABLE Discussion_Forum (
    forumId INT AUTO_INCREMENT PRIMARY KEY,
    courseId VARCHAR(255) NOT NULL,
    forumTitle VARCHAR(255) NOT NULL,
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Discussion_Thread (
    threadId INT AUTO_INCREMENT PRIMARY KEY,
    forumId INT,
    userId INT,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    datePosted DATE NOT NULL,
    FOREIGN KEY (userId) REFERENCES User(userId),
    FOREIGN KEY (forumId) REFERENCES Discussion_Forum(forumId)
);

CREATE TABLE Creates (
    adminId INT,
    courseId VARCHAR(255),
    PRIMARY KEY (adminId, courseId),
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Posts (
    postId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT,
    threadId INT,
    content TEXT NOT NULL,
    datePosted DATE NOT NULL,
    parentPostId INT DEFAULT NULL,
    FOREIGN KEY (userId) REFERENCES User(userId),
    FOREIGN KEY (threadId) REFERENCES Discussion_Thread(threadId),
    FOREIGN KEY (parentPostId) REFERENCES Posts(postId)
);


CREATE TABLE Section (
    sectionId INT AUTO_INCREMENT PRIMARY KEY ,
    courseId VARCHAR(255),
    sectionTitle VARCHAR(255) NOT NULL,
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

CREATE TABLE Content (
    contentID INT AUTO_INCREMENT PRIMARY KEY ,
    sectionId INT,
    link VARCHAR(255),
    file VARCHAR(255),
    slide VARCHAR(255),
    FOREIGN KEY (sectionId) REFERENCES Section(sectionId)
);

CREATE TABLE Calendar_Events (
    eventId INT AUTO_INCREMENT PRIMARY KEY,
    courseId VARCHAR(255),
    beginning DATE NOT NULL,
    end DATE NOT NULL,
    eventTitle VARCHAR(255) NOT NULL,
    FOREIGN KEY (courseId) REFERENCES Course(courseId)
);

-- Indexes --

CREATE INDEX idx_enrols_student_id ON Enrols(studentId);

CREATE INDEX idx_enrols_course_id ON Enrols(courseId);

CREATE INDEX idx_course_id ON Course(courseId);

CREATE INDEX idx_user_id ON User(userId);

CREATE INDEX idx_lecturer_id ON Lecturer(lecturerId);

CREATE INDEX idx_student_id ON Student(studentId);

CREATE INDEX idx_assignment_id ON Assignment(assignmentId);

CREATE INDEX idx_admin_id ON Admin(adminId);

CREATE INDEX idx_teaches_course_id ON Teaches(courseId);

CREATE INDEX idx_teaches_lecturer_id ON Teaches(lecturerId);


-- Views --

CREATE VIEW courses_50_over AS
SELECT c.courseId, c.courseTitle, COUNT(e.studentId)
    FROM Course c
    JOIN Enrols e ON c.courseId = e.courseId
    GROUP BY c.courseId
    HAVING COUNT(e.studentId) >= 50;

CREATE VIEW student_course_5_over AS
    SELECT e.studentId, u.firstName, u.lastName ,COUNT(e.courseId), s.dateOfBirth
    FROM Enrols e
    JOIN Student s ON s.studentId = e.studentId
    JOIN User u ON s.studentId = u.userId
    GROUP BY e.studentId
    HAVING COUNT(e.courseId) >= 5;

CREATE VIEW lecturer_teach_3_over AS
SELECT t.lecturerId, u.firstName, u.lastName, l.department,COUNT(c.courseId)
    FROM Course c
    JOIN Teaches t ON t.courseId = c.courseId
    JOIN Lecturer l on l.lecturerId = t.lecturerId
    JOIN User u on u.userId = l.lecturerId
    GROUP BY t.lecturerId
    HAVING COUNT(c.courseId) >= 3;

CREATE VIEW top10courses AS
SELECT c.courseId, c.courseTitle, COUNT(e.studentId) AS studentCount
    FROM Course c
    JOIN Enrols e ON c.courseId = e.courseId
    GROUP BY c.courseId, c.courseTitle
    ORDER BY studentCount DESC
    LIMIT 10;

CREATE VIEW top10students AS
SELECT s.studentId, u.firstName, u.lastName, AVG(IFNULL(e.grade, 0)) AS averageGrade
    FROM Student s
    JOIN Enrols e ON s.studentId = e.studentId
    JOIN User u ON u.userId = s.studentId
    GROUP BY s.studentId
    ORDER BY averageGrade DESC
    LIMIT 10;



-- inserts

SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertUsers.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertAdmins.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertLecturers.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertStudents.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertCourses.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertTeaches.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertCreates.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertEnrols.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertAssignments.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertSubmits.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertForums.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/inserThreads.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertSections.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertContents.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insertEvents.sql;
SOURCE  C:/Users/forde/Downloads/Final Project (1)/Final Project/insert_replies.sql;