from django.http import HttpRequest
from django.db.models import Model
from typing import Literal
from django.contrib.contenttypes.models import ContentType

def hasPermission (
        request: HttpRequest,
        model: Model,
        type: Literal["view", "add", "change", "delete"]
) -> bool: 
    """
    Checks if user has the given permission to the given django model.

    Parameters
    ----------
    request : HttpRequest
        The http request, containing the user session info.
    model : The django model for which to check the permission
    type : str
        The type of permissions to check.  Options are 'view', 'add', 'change', 'delete'.

    Returns
    -------
    bool
        True if user's group has the permission otherwise false.
    """
    
    user = request.user    
    groups = user.groups.all()

    if user.is_staff:
        return True

    if not groups:
        return False
    
    permissionCodename = f"{type}_{model._meta.model_name}"
    contentType = ContentType.objects.get_for_model(model)

    for group in groups:
        permissions = group.permissions.filter(codename=permissionCodename, content_type=contentType)
        if permissions.exists():
            return True
    
    return False

def canApprovePD (request: HttpRequest):
    user = request.user
    
    #Users are maunally allowed to approve PD
    authorizedUsers = ['tanveer', 'firasat']
    if user.username in authorizedUsers:
        return True
    
    #if user is server admin, they can access PD approval
    if user.is_staff:
        return True

    return False