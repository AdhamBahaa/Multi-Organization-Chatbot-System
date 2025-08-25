# Feedback Feature Documentation

## Overview

The feedback feature allows users to rate and provide comments on chatbot responses, while admins can view and analyze this feedback to improve the system.

## Features

### For Users

- **Rate Responses**: Users can rate each chatbot response on a 1-5 star scale
- **Add Comments**: Optional text comments to provide detailed feedback
- **Visual Feedback**: Clear indication when feedback has been submitted
- **Easy Access**: Feedback button appears on every bot response

### For Admins

- **View All Feedback**: See feedback from all users in their organization
- **Statistics Dashboard**: View overall feedback statistics and rating distribution
- **Filter and Sort**: Filter by rating and sort by date, rating, or user
- **Detailed View**: See the full conversation context for each feedback entry

## Database Schema

### Feedback Table

```sql
CREATE TABLE Feedback (
    FeedbackID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT NOT NULL,
    OrganizationID INT NOT NULL,
    SessionID INT NOT NULL,
    MessageID INT NOT NULL,
    UserMessage NVARCHAR(MAX) NOT NULL,
    BotResponse NVARCHAR(MAX) NOT NULL,
    Rating INT NOT NULL,
    Comment NVARCHAR(MAX) NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (OrganizationID) REFERENCES Organizations(OrganizationID)
);
```

## API Endpoints

### Submit Feedback

- **POST** `/api/feedback/submit`
- **Access**: Users only
- **Body**:
  ```json
  {
    "session_id": 123,
    "message_id": 456,
    "user_message": "What is AI?",
    "bot_response": "AI is artificial intelligence...",
    "rating": 5,
    "comment": "Very helpful response!"
  }
  ```

### Get User's Feedback

- **GET** `/api/feedback/my-feedback`
- **Access**: Users only
- **Response**: List of user's submitted feedback

### Get Users' Feedback (Admin)

- **GET** `/api/feedback/admin/users-feedback`
- **Access**: Admins only
- **Response**: List of feedback from all users managed by the admin

### Get Feedback Statistics

- **GET** `/api/feedback/admin/feedback-stats`
- **Access**: Admins only
- **Response**:
  ```json
  {
    "total_feedback": 25,
    "average_rating": 4.2,
    "rating_distribution": {
      "1": 2,
      "2": 3,
      "3": 5,
      "4": 8,
      "5": 7
    },
    "total_users": 10
  }
  ```

## Frontend Components

### Chat Component Updates

- Added feedback button to each bot response
- Feedback modal with star rating and comment input
- Visual confirmation when feedback is submitted

### FeedbackManager Component

- Comprehensive feedback management interface for admins
- Statistics dashboard with charts and metrics
- Filtering and sorting capabilities
- Detailed feedback view with conversation context

## Setup Instructions

### 1. Create Database Table

Run the database migration script:

```bash
cd backend
python create_feedback_table.py
```

### 2. Restart Backend Server

The new routes will be automatically loaded.

### 3. Test the Feature

1. Login as a user and send a message to the chatbot
2. Click the "Rate Response" button on the bot's response
3. Provide a rating and optional comment
4. Submit the feedback
5. Login as an admin to view the feedback in the dashboard

## Usage Guide

### For Users

1. **Chat with the Bot**: Send messages and receive responses
2. **Rate Responses**: Click the ⭐ "Rate Response" button on any bot response
3. **Provide Rating**: Select 1-5 stars based on response quality
4. **Add Comment**: Optionally add detailed feedback
5. **Submit**: Click "Submit Feedback" to save your rating

### For Admins

1. **Access Feedback**: Go to Admin Dashboard → ⭐ Feedback tab
2. **View Statistics**: See overall feedback metrics and rating distribution
3. **Filter Feedback**: Use the filter dropdown to view specific ratings
4. **Sort Results**: Sort by date, rating, or user name
5. **Analyze Responses**: Click on feedback items to see full conversation context

## Rating System

- **5 Stars (Excellent)**: Perfect response, very helpful
- **4 Stars (Very Good)**: Good response with minor issues
- **3 Stars (Good)**: Adequate response, meets basic needs
- **2 Stars (Fair)**: Response has some issues or is incomplete
- **1 Star (Poor)**: Unhelpful or incorrect response

## Security Features

- **Role-based Access**: Only users can submit feedback, only admins can view
- **Organization Isolation**: Admins only see feedback from their organization's users
- **Input Validation**: Rating must be 1-5, comments limited to 500 characters
- **Authentication Required**: All endpoints require valid JWT tokens

## Future Enhancements

- **Feedback Analytics**: Advanced analytics and reporting
- **Response Improvement**: Use feedback to improve AI responses
- **Notification System**: Alert admins of low-rated responses
- **Export Functionality**: Export feedback data for external analysis
- **Trend Analysis**: Track feedback trends over time

## Troubleshooting

### Common Issues

1. **Feedback button not appearing**

   - Ensure you're logged in as a user (not admin)
   - Check that the response is from the bot (not user messages)

2. **Cannot submit feedback**

   - Verify you have a valid session
   - Check that you've selected a rating (1-5 stars)
   - Ensure the comment is under 500 characters

3. **Admin cannot see feedback**

   - Verify you're logged in as an admin
   - Check that users in your organization have submitted feedback
   - Ensure the backend server is running

4. **Database errors**
   - Run the migration script: `python create_feedback_table.py`
   - Check database connection and permissions
   - Verify the Feedback table exists in your database

### Support

For technical issues, check the backend logs and browser console for error messages.
