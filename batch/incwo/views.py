from core.decorator import pydici_feature

from django.shortcuts import render


@pydici_feature("management")
def imports(request):
    return render(request, "incwo/imports.html")
