"""Permisos base y límites delegables por rol. No se confía en el navegador."""
from fastapi import HTTPException

PERMISSIONS = {
    'catalog.read': 'Consultar catálogo',
    'orders.create': 'Crear pedidos',
    'orders.read_own': 'Consultar pedidos propios',
    'quotes.create': 'Solicitar cotizaciones',
    'quotes.read_own': 'Consultar cotizaciones propias',
    'profile.read': 'Consultar perfil propio',
    'delivery.read_assigned': 'Consultar entregas asignadas',
    'delivery.start': 'Despachar e iniciar recorrido',
    'delivery.complete': 'Confirmar entrega',
    'delivery.issue': 'Registrar novedad',
    'products.manage': 'Gestionar productos e inventario',
    'orders.manage': 'Gestionar pedidos y asignaciones',
    'quotes.manage': 'Gestionar cotizaciones',
    'content.manage': 'Gestionar contenido institucional',
    'access.manage': 'Gestionar roles y permisos',
    'users.manage': 'Gestionar usuarios y registrar mensajeros',
    'appearance.manage': 'Gestionar apariencia de la empresa',
}
ROLE_PERMISSIONS = {
    'cliente': ['catalog.read', 'orders.create', 'orders.read_own', 'quotes.create', 'quotes.read_own', 'profile.read'],
    'mensajeria': ['delivery.read_assigned', 'delivery.start', 'delivery.complete', 'delivery.issue', 'profile.read'],
    'admin': list(PERMISSIONS),
    'propietario': list(PERMISSIONS),
    'vendedor': ['catalog.read', 'profile.read', 'products.manage', 'orders.manage', 'quotes.manage'],
}
CUSTOM_ROLE_PERMISSIONS = [code for code in PERMISSIONS if code not in {'access.manage', 'users.manage', 'appearance.manage'}]
DELIVERY_STATUS_PERMISSIONS = {
    'en_ruta': 'delivery.start',
    'entregado': 'delivery.complete', 'novedad': 'delivery.issue',
}


def has_permission(user: dict, permission: str) -> bool:
    # Solo los usuarios construidos por el servidor llegan aquí. La ausencia de
    # lista admite los permisos base para servicios internos y pruebas locales.
    return permission in user.get('permissions', ROLE_PERMISSIONS.get(user.get('role'), []))


def can_read_order(user: dict, order: dict) -> bool:
    return (
        has_permission(user, 'orders.manage')
        or (has_permission(user, 'orders.read_own') and order.get('user_id') == user.get('id'))
        or (has_permission(user, 'delivery.read_assigned') and order.get('assigned_delivery_user_id') == user.get('id'))
    )


def authorize_delivery_update(user: dict, order: dict, status: str):
    if has_permission(user, 'orders.manage'):
        return
    if not can_read_order(user, order):
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    permission = DELIVERY_STATUS_PERMISSIONS.get(status)
    if not permission or not has_permission(user, permission):
        raise HTTPException(status_code=403, detail='No tienes permiso para realizar este cambio logístico')
    transitions = {
        'en_ruta': {'en_preparacion', 'empacado', 'despachado'},
        'entregado': {'en_ruta'},
        'novedad': {'en_preparacion', 'empacado', 'despachado', 'en_ruta'},
    }
    if order.get('order_status') not in transitions[status]:
        raise HTTPException(status_code=409, detail='El estado actual no permite esta transición logística')


def project_order(user: dict, order: dict) -> dict:
    if has_permission(user, 'orders.manage') or (has_permission(user, 'orders.read_own') and order.get('user_id') == user.get('id')):
        return order
    allowed = ['id', 'order_number', 'customer_name', 'customer_phone', 'address', 'order_status',
               'notes', 'assigned_delivery_user_id', 'tracking_history', 'created_at']
    return {**{key: order.get(key) for key in allowed}, 'items': [
        {'product_name': item.get('product_name'), 'quantity': item.get('quantity')}
        for item in order.get('items', [])]}
