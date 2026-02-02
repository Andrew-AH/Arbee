from enum import Enum


class Vendor(Enum):
    VENDOR_ALPHA = "VendorAlpha"
    VENDOR_BETA = "VendorBeta"
    VENDOR_GAMMA = "VendorGamma"
    VENDOR_DELTA = "VendorDelta"


class Service(Enum):
    CLIENT = "Client"
    SCRAPER = "Scraper"
    EXECUTOR = "Executor"
    DETECTOR = "Detector"
