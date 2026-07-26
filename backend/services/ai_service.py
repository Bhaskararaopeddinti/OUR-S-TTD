def pilgrim_reply(message: str, language: str = "English") -> str:
    query = message.lower()
    if any(x in query for x in ("queue", "wait", "darshan")):
        return "Sarva Darshan is currently estimated at about 2 hours 15 minutes. The least busy window is usually early afternoon."
    if any(x in query for x in ("phone", "mobile")):
        return "Mobile phones are prohibited inside the temple. Deposit them at centres opposite VQC I and II, PAC-3, PAC-5, or near darshan lines. Confirm your collection point and retain the receipt token."
    if any(x in query for x in ("restroom", "toilet", "washroom")):
        return "Restrooms and drinking water are available across PAC I–V, VQC I and II, Kalyanakatta, and Jala Prasadam RO kiosks on the temple ring road."
    if any(x in query for x in ("food", "annaprasadam")):
        return "Annaprasadam is available at the Matrusri Tarigonda Vengamamba Annaprasada Complex, VQC compartments, PAC II, Rambagicha Bus Stand, and CRO. Please confirm the nearest open counter with a volunteer."
    return "Namaste. I can help with queue status, temple etiquette, food, facilities, phone deposit, health support and navigation. What do you need?"
