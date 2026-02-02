from datetime import datetime


def make_execution_success_message(
    venue_name: str,
    event_time: datetime,
    profit_in_dollars: float,
    percentage_return: float,
    item: str,
    sell_price: float,
    sell_amount: float,
    sell_liquidity: float,
    buy_price: float,
    buy_amount: float,
    detected_timestamp: datetime,
    executed_timestamp: datetime,
):
    return (
        " Execution Successful! \n"
        f"  -  Event: {venue_name} {event_time:%m-%d %H:%M}\n"
        f"  -  Profit: ${profit_in_dollars:,.2f} ({percentage_return:.2%})\n"
        f"  -  Sell Liquidity: ${sell_liquidity:,.2f}\n"
        f"  -  Sold: ${sell_amount:,.2f} @ {sell_price}\n"
        f"  -  Bought: ${buy_amount:,.2f} @ {buy_price}\n"
        f"  -  Item: {item}\n"
        f"  -  Detected: {detected_timestamp:%Y-%m-%d %H:%M:%S}\n"
        f"  -  Executed: {executed_timestamp:%Y-%m-%d %H:%M:%S}\n"
    )


def make_order_placed_message(
    venue_name: str,
    event_time: datetime,
    item: str,
    amount: float,
    profit_percentage: float,
    account_username: str,
    machine: str,
    detected_timestamp: datetime,
    executed_timestamp: datetime,
):
    embed = {
        "title": "Order Placed",
        "color": 21312,
        "fields": [
            {"name": "Amount", "value": f"${amount:,.2f}", "inline": True},
            {
                "name": "Venue",
                "value": f"{venue_name} {event_time.strftime('%H:%M')}",
                "inline": True,
            },
            {"name": "Item", "value": item, "inline": True},
            {
                "name": "Profit",
                "value": f"{profit_percentage * 100:,.2f}%",
                "inline": True,
            },
            {
                "name": "Detected",
                "value": detected_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True,
            },
            {
                "name": "Executed",
                "value": executed_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True,
            },
            {
                "name": "Machine",
                "value": machine,
                "inline": True,
            },
        ],
    }

    return {"username": account_username, "embeds": [embed]}


def make_todays_events_message(
    enriched_venues: dict[str, list[tuple[str, int, int, datetime]]],
) -> str:
    lines = [f"__**Events for {datetime.now().strftime('%d/%m/%Y')}**__\n"]
    total_events = 0

    for venue, events in enriched_venues.items():
        if len(events) != 0:
            times = [f"` {dt.strftime('%H:%M')} `" for *_, dt in events]
            time_line = " ".join(times)
            total_events += len(events)
            lines.append(f"**{venue} ({len(events)} events)**\n{time_line}\n")

    lines.append(f"**Total events: {total_events}**")

    return "\n".join(lines)
