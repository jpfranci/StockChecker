from typing import List

# chunks messages according to discord max message length
def chunk_messages(messages: List[str], new_lines_to_add: int = 0) -> List[str]:
    message_chunks = []
    current_message_chunk = ""
    for message in messages:
        if len(current_message_chunk) + len(message) < 2000:
            if current_message_chunk != "":
                for n in range(new_lines_to_add):
                    new_lines_to_add += "\n"
            current_message_chunk += message
        else:
            message_chunks.append(current_message_chunk)
            current_message_chunk = message

    if current_message_chunk != "":
        message_chunks.append(current_message_chunk)
    return message_chunks