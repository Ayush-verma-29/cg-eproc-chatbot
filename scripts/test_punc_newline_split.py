# scripts/test_punc_newline_split.py
import re

def get_complete_sentences_and_newlines(buffer: str) -> tuple:
    pattern = re.compile(
        r'(\n+)|((?<!\bRs)(?<!\bNo)(?<!\bno)(?<!\bJan)(?<!\bFeb)(?<!\bMar)(?<!\bApr)(?<!\bJun)(?<!\bJul)(?<!\bAug)(?<!\bSep)(?<!\bOct)(?<!\bNov)(?<!\bDec)(?<!\b[A-Za-z])(?<!\b\d)[.!?](?:\s+|\n+))'
    )
    
    matches = list(pattern.finditer(buffer))
    if not matches:
        return [], buffer
        
    parts = []
    last_idx = 0
    for match in matches:
        text_segment = buffer[last_idx:match.start()].strip()
        if text_segment:
            parts.append(text_segment)
            
        match_str = match.group(0)
        if '\n' in match_str:
            if match_str[0] in '.!?':
                punc = match_str[0]
                if parts and not parts[-1].startswith('\n'):
                    parts[-1] += punc
                elif text_segment:
                    parts[-1] += punc
            newlines_count = match_str.count('\n')
            parts.append('\n' * newlines_count)
        else:
            punc = match_str[0]
            if parts and not parts[-1].startswith('\n'):
                parts[-1] += punc
            elif text_segment:
                parts[-1] += punc
                
        last_idx = match.end()
        
    remaining = buffer[last_idx:]
    return parts, remaining

def test():
    text = (
        "Here are the different methods:\n\n"
        "1. Direct Purchase: applicable when less than Rs. 50,000. In this case, there is no need [Page 132].\n\n"
        "2. L1 Purchase: applicable above Rs. 50,000. Buyers must select L1 [Page 132]."
    )
    
    print("Original Text:")
    print(repr(text))
    print("\nSplitting...")
    parts, remaining = get_complete_sentences_and_newlines(text + " ") # simulate trailing space at end of stream
    
    print("\nSplit Parts:")
    for idx, part in enumerate(parts):
        print(f"Part {idx}: {repr(part)}")
    print(f"Remaining: {repr(remaining)}")

if __name__ == "__main__":
    test()
