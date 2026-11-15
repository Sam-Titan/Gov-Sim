from fastapi import Request

from govsim.service import Service


def get_service(request: Request) -> Service:
    return request.app.state.service
