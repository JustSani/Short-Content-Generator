def parse_time_str(time_str: str) -> int:
    """
    Converte una stringa 'mm:ss' o 'ss' in secondi interi.
    Es: '01:30' -> 90
    Es: '45' -> 45
    """
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return (minutes * 60) + seconds
        elif len(parts) == 3: # Gestisce anche h:mm:ss
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return (hours * 3600) + (minutes * 60) + seconds
    
    return int(time_str)