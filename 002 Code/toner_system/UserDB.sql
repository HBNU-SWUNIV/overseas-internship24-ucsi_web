
-- Create UserDB and Users table
CREATE DATABASE UserDB;

USE UserDB;

CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    UserName VARCHAR(50) NOT NULL,
    UserLoginID VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    Department VARCHAR(50)
);

-- Insert dummy data into Users table
INSERT INTO Users (UserName, UserLoginID, PasswordHash, Department)
VALUES ('John Doe', 'johndoe', 'hashed_password_1', 'HR'),
       ('Jane Smith', 'janesmith', 'hashed_password_2', 'IT'),
       ('Emily Johnson', 'emilyj', 'hashed_password_3', 'Marketing'),
       ('Michael Brown', 'michaelb', 'hashed_password_4', 'Sales'),
       ('Sarah Davis', 'sarahd', 'hashed_password_5', 'Finance');
