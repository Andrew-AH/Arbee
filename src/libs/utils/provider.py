from typing import Dict, Type
from libs.utils.enums import Vendor, Service
from libs.vendors.vendor_alpha.detector import VendorAlphaDetector
from libs.vendors.vendor_alpha.executor import VendorAlphaExecutor


class ServiceNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


vendor_service_registry: Dict[Vendor, Dict[Service, Type]] = {
    Vendor.VENDOR_ALPHA: {Service.EXECUTOR: VendorAlphaExecutor, Service.DETECTOR: VendorAlphaDetector}
}


def get_service(vendor: Vendor, service: Service) -> Type:
    try:
        vendor_services = vendor_service_registry[vendor]
    except KeyError:
        raise ServiceNotFoundError(f"Vendor '{vendor.name}' is not defined in the service mapping.")

    try:
        return vendor_services[service]
    except KeyError:
        raise ServiceNotFoundError(
            f"Service '{service.name}' for vendor '{vendor.name}' is not defined in the service mapping."
        )
