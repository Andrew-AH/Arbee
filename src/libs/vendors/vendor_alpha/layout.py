class XPath:
    # PAGE: ALL
    LOGIN_BUTTON = (
        "//div[@class='hm-MainHeaderRHSLoggedOutWide_Badge hm-MainHeaderRHSLoggedOutWide_Login ']"
    )
    USER_INFO_BALANCE = "//div[contains(@class, 'hm-MainHeaderMembersWide_Balance')]"
    ACCEPT_COOKIES_BUTTON = "//button[@class='rcc-c']"
    REJECT_COOKIES_BUTTON = "//button[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'essential only']"

    # PAGE: LOGIN MODAL
    USER_NAME_INPUT = "//input[@class='lms-StandardLogin_Username ']"
    PASSWORD_INPUT = "//input[@class='lms-StandardLogin_Password ']"
    MODAL_LOGIN_BUTTON = "//div[@class='lms-LoginButton ']"

    # PAGE: EVENT
    CURRENT_EVENT_NUMBER = "//div[contains(@class, 'srl-ParticipantEventTab-selected')]"
    RUNNER = "//div[@class='srm-ParticipantItemFixed gl-Market_General-cn1 ']"
    EVENT_INFO = "//div[@class='srl-MarketEventHeaderInfo_InfoContainer ']"
    EVENT_NUMBERS_CONTAINER = "//div[@class='srl-PillNavScroller_Contents ']"
    VENUE_NAME = "//div[@class='srl-EventDropDown_Button ']"

    # PAGE: ORDER SLIP MODAL
    PLACE_ORDER_BUTTON = "//div[contains(@class, 'bsf-PlaceOrderButton_TopRow')]"
    CONFIRMATION_RECEIPT = "//div[contains(@class, 'bsm-ReceiptContent_Title ')]"
    CONFIRMATION_RECEIPT_REFERENCE_NUMBER = "//div[contains(@class, 'bsm-ReceiptContent_OrderRef ')]"
    ORDER_CONFIRMATION_RECEIPT_REMOVE_BUTTON = "//div[@class='bsm-ReceiptContent_Done ']"
    AMOUNT_BOX_REMOVE_BUTTON = "//div[@class='bss-RemoveButton ']"
    AMOUNT_BOX_AMOUNT_INPUT_NOT_SET = "//div[@class='bsf-AmountBox_AmountValue bsf-AmountBox_AmountValue-input bsf-AmountBox_AmountValue-empty ']"
    AMOUNT_BOX_AMOUNT_VALUE = (
        "//div[contains(@class, 'bsf-AmountBox_AmountValue bsf-AmountBox_AmountValue-input ')]"
    )
    AMOUNT_BOX_REMEMBER_BUTTON = "//div[@class='bsf-RememberAmountButtonNonTouch_HitArea ']"
    AMOUNT_BOX_REMEMBER_BUTTON_ACTIVE = (
        "//div[@class='bsf-RememberAmountButtonNonTouch bsf-RememberAmountButtonNonTouch-active ']"
    )
    AMOUNT_BOX_PRICE = "//span[contains(@class, 'bsm-AusPriceLabel')]"
    ORDER_NEEDS_APPROVAL_MESSAGE = "//div[@class='bs-OrderslipReferralsMessage_Title ']"


class ClassName:
    RUNNER_NAME_CLASS = "srm-ParticipantDetailsItemFixed_RunnerName "
    BUY_PRICE = "srm-ParticipantItemPriceFixed_Price"
