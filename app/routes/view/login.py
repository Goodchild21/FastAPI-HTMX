from fastapi import Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.routing import APIRouter
from fastapi_csrf_protect import CsrfProtect

from app.database.security import current_active_user, verify_jwt
from app.models.users import User as UserModelDB
from app.templates import templates

#
from app.routes.view.view_crud import SQLAlchemyCRUD
from app.models.groups import Group as GroupModelDB
from app.database.db import CurrentAsyncSession
from app.models.users import Role as UserRoleModelDB
from app.models.users import UserProfile as UserProfileModelDB

# Create an APIRouter
login_view_route = APIRouter()

#
# group_view_route = APIRouter()
group_crud = SQLAlchemyCRUD[GroupModelDB](
    GroupModelDB, related_models={UserModelDB: "users"}
)
user_crud = SQLAlchemyCRUD[UserModelDB](
    UserModelDB,
    related_models={UserProfileModelDB: "profile", UserRoleModelDB: "role"},
)


# Defining a route to navigate to the dashboard page using the current_active_user dependency
@login_view_route.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(
    request: Request,
    db: CurrentAsyncSession, #
    user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    groups = await group_crud.read_all(db, join_relationships=True)

    # Access the cookies using the Request object
    cookies = request.cookies
    cookie_value = cookies.get("fastapiusersauth")
    response = templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "title": "FastAPI-HTMX",
            "message": f"Welcome to FastAPI-HTMX!{user.email}",
            "cookie_value": cookie_value,
            "csrf_token": csrf_token,
            "user_type": user.is_superuser,
            "groups": groups, #
        },
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@login_view_route.get("/")
async def get_index(request: Request, csrf_protect: CsrfProtect = Depends()):
    cookies = request.cookies
    cookie_value = cookies.get("fastapiusersauth")
    if cookie_value is not None:
        if await verify_jwt(cookie_value):
            return RedirectResponse("/dashboard", status_code=302)
        else:
            return RedirectResponse("/login", status_code=302)
    else:
        return RedirectResponse("/login", status_code=302)


@login_view_route.get(
    "/login",
    summary="Gets the login page",
    tags=["Pages", "Authentication"],
    response_class=HTMLResponse,
)
async def get_login(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
):
    current_page = request.url.path.split("/")[-1]
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    context = {
        "request": request,
        "current_page": current_page,
        "csrf_token": csrf_token,
    }

    response = templates.TemplateResponse("pages/login.html", context)

    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@login_view_route.get(
    "/register",
    summary="Gets the login page",
    tags=["Pages", "Register USer"],
    response_class=HTMLResponse,
)
async def get_register(
    request: Request,
):
    current_page = request.url.path.split("/")[-1]
    context = {
        "request": request,
        "current_page": current_page,
    }
    return templates.TemplateResponse("pages/register.html", context)
