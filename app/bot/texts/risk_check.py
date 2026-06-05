"""Text constants and templates for token risk check messages."""

RISK_CHECK_MENU_TEXT = (
    "🛡 <b>Token risk check</b>\n\n"
    "Send a smart contract address and I will check it for risky contract "
    "behavior."
)

RISK_CHECK_ENTER_CHAIN_TEXT = (
    "🌐 <b>Choose blockchain</b>\n\nSelect the network where the token contract exists."
)

RISK_CHECK_ENTER_ADDRESS_TEXT = (
    "🔎 <b>Send contract address</b>\n\n"
    "Example: <code>0x0000000000000000000000000000000000000000</code>"
)

RISK_CHECK_LOADING_TEXT = (
    "🔎 <b>Checking token</b>\n\n"
    "I am checking the contract address for risk signals. This can take a moment."
)

RISK_CHECK_CANCELLED_TEXT = "Token risk check cancelled."

RISK_CHECK_FAILED_TEXT = (
    "⚠️ I could not check this token right now.\n\nPlease try again later."
)

RISK_CHECK_TOKEN_NOT_FOUND_TEXT = (
    "⚠️ <b>Token data was not found on this network</b>\n\n"
    "Please check that you selected the correct blockchain for this contract "
    "address and try again."
)

INVALID_CONTRACT_ADDRESS_TEXT = (
    "Invalid contract address.\n\n"
    "Please send a valid EVM contract address starting with <code>0x</code>."
)

NO_NORMALIZED_RISK_FLAGS_TEXT = "No normalized risk signals were detected."

TOKEN_CHECK_RESULT_TEMPLATE = (
    "🛡 <b>Token risk report</b>\n\n"
    "<b>Chain:</b> {chain}\n"
    "<b>Contract:</b> <code>{contract_address}</code>\n"
    "Risk level: <b>{risk_level}</b>\n\n"
    "<b>Detected signals:</b>\n"
    "{signals}\n\n"
    "⚠️ This report is based on automated checks and does not guarantee that "
    "the token is safe."
)

TOKEN_RISK_SIGNAL_TEMPLATE = "• {name}: {value}"

TOKEN_RISK_BOOLEAN_VALUE_LABEL = "detected"
TOKEN_RISK_PERCENT_VALUE_TEMPLATE = "{value}%"

TOKEN_RISK_SIGNAL_LABELS: dict[str, str] = {
    "is_honeypot": "Honeypot behavior",
    "cannot_sell_all": "Cannot sell all tokens",
    "is_blacklisted": "Blacklist function",
    "is_proxy": "Proxy contract",
    "hidden_owner": "Hidden owner",
    "slippage_modifiable": "Sell tax can be changed",
    "personal_slippage_modifiable": "Personal tax can be changed",
    "selfdestruct": "Self-destruct function",
    "owner_change_balance": "Owner can change balances",
    "can_take_back_ownership": "Owner can take back ownership",
    "is_mintable": "Mintable supply",
    "external_call": "External contract calls",
    "trading_cooldown": "Trading cooldown",
    "buy_tax": "Buy tax",
    "sell_tax": "Sell tax",
}
