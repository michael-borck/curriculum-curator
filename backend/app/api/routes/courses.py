"""
Course management routes
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def get_courses(skip: int = 0, limit: int = 100):
    """
    Get all courses for the current user.
    """
    # Mock data for testing
    return [
        {
            "id": 1,
            "title": "Introduction to Computer Science",
            "code": "CS101",
            "weeks": 12,
            "items": 45,
            "progress": 75,
        },
        {
            "id": 2,
            "title": "Data Structures & Algorithms",
            "code": "CS201",
            "weeks": 12,
            "items": 38,
            "progress": 60,
        },
    ]


@router.get("/{course_id}")
async def get_course(course_id: int):
    """
    Get a specific course by ID.
    """
    if course_id == 1:
        return {
            "id": 1,
            "title": "Introduction to Computer Science",
            "code": "CS101",
            "weeks": 12,
            "items": 45,
            "progress": 75,
            "description": "An introduction to the fundamental concepts of computer science.",
        }

    raise HTTPException(status_code=404, detail="Course not found")


@router.post("/")
async def create_course(title: str, code: str, weeks: int):
    """
    Create a new course.
    """
    return {
        "id": 3,
        "title": title,
        "code": code,
        "weeks": weeks,
        "items": 0,
        "progress": 0,
    }
