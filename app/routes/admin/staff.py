from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import hash_password
from app.common import PaginatedResponse
from app.models.staff import Staff
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate
from app.database.db import get_db
from app.deps import pagination_params, require_superuser

router = APIRouter(prefix="/admin/staff", tags=["admin-staff"])


def build_accesses(staff: Staff) -> dict:
    return {
        "can_access_user": staff.can_access_user,
        "can_access_staff": staff.can_access_staff,
        "can_access_property": staff.can_access_property,
        "can_add_property": staff.can_add_property,
        "can_edit_property": staff.can_edit_property,
        "can_delete_property": staff.can_delete_property,
        "can_unlist_property": staff.can_unlist_property,
    }


@router.post("/", response_model=StaffResponse)
def create_staff(
    staff: StaffCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_superuser)
):
    # Check if email already exists in the staff table
    existing_staff = db.query(Staff).filter(Staff.email == staff.email).first()
    if existing_staff:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the staff password before saving it
    hashed_password = hash_password(staff.password)

    # Ensure the admin_user has a valid user_id (the user that creates this staff)
    if not admin_user:  # Ensure the admin_user exists
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Create new staff member with admin's user_id as the creator
    new_staff = Staff(
        name=staff.name,
        email=staff.email,
        phone=staff.phone,
        password=hashed_password,  # Use the hashed password here
        role=staff.role,
        user_id=admin_user.id,  # Ensure this is set to an existing user in the users table
        can_access_user=staff.can_access_user,
        can_access_staff=staff.can_access_staff,
        can_access_property=staff.can_access_property,
        can_add_property=staff.can_add_property,
        can_edit_property=staff.can_edit_property,
        can_delete_property=staff.can_delete_property,
        can_unlist_property=staff.can_unlist_property,
    )

    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    return StaffResponse(
        id=new_staff.id,
        name=new_staff.name,
        email=new_staff.email,
        phone=new_staff.phone,
        role=new_staff.role,
        accesses=build_accesses(new_staff),
    )



# Get all Staff
@router.get("/", response_model=PaginatedResponse[StaffResponse])
def list_staff(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_superuser),
    params: dict = Depends(pagination_params),
    
):
    
    query = db.query(Staff)

    # Apply pagination parameters (offset and limit)
    staff_members = query.offset((params["page"] - 1) * params["limit"]).limit(params["limit"]).all()

    # Get the total number of staff members (without pagination)
    total = db.query(Staff).count()
    
    data = [
    StaffResponse(
            id=s.id,
            name=s.name,
            email=s.email,
            phone=s.phone,
            role=s.role,
            accesses=build_accesses(s),
        )
        for s in staff_members
    ]

    return {
        "data": data,
        "pagination": {
            "page": params["page"],
            "limit": params["limit"],
            "total": total,
        }
    }


# Get Staff by ID
@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    
    staff_member = db.query(Staff).filter(Staff.id == staff_id).first()

    if not staff_member:
        raise HTTPException(status_code=404, detail="Staff member not found")

    return StaffResponse(
        id=staff_member.id,
        name=staff_member.name,
        email=staff_member.email,
        phone=staff_member.phone,
        role=staff_member.role,
        accesses=build_accesses(staff_member),
    )


# Update Staff
@router.patch("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: UUID,
    staff_update: StaffUpdate,  # Use the StaffUpdate schema
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    staff_member = db.query(Staff).filter(Staff.id == staff_id).first()

    if not staff_member:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # Update only fields that are provided in the request
    if staff_update.name is not None:
        staff_member.name = staff_update.name
    if staff_update.email is not None:
        staff_member.email = staff_update.email
    if staff_update.phone is not None:
        staff_member.phone = staff_update.phone
    if staff_update.role is not None:
        staff_member.role = staff_update.role
    if staff_update.password is not None:
        staff_member.password = staff_update.password  
    if staff_update.can_access_user is not None:
        staff_member.can_access_user = staff_update.can_access_user
    if staff_update.can_access_staff is not None:
        staff_member.can_access_staff = staff_update.can_access_staff
    if staff_update.can_access_property is not None:
        staff_member.can_access_property = staff_update.can_access_property
    if staff_update.can_add_property is not None:
        staff_member.can_add_property = staff_update.can_add_property
    if staff_update.can_edit_property is not None:
        staff_member.can_edit_property = staff_update.can_edit_property
    if staff_update.can_delete_property is not None:
        staff_member.can_delete_property = staff_update.can_delete_property
    if staff_update.can_unlist_property is not None:
        staff_member.can_unlist_property = staff_update.can_unlist_property

    db.commit()
    db.refresh(staff_member)

    return staff_member


@router.delete("/{staff_id}", response_model=dict)
def delete_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    staff_member = db.query(Staff).filter(Staff.id == staff_id).first()

    if not staff_member:
        raise HTTPException(status_code=404, detail="Staff member not found")

    db.delete(staff_member)
    db.commit()

    return {"message": "Staff member deleted successfully"}