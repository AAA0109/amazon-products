def split(lst, n):
    """
    Splits a list into n roughly equal-sized sublists.

    Args:
        lst (list): The list to be split.
        n (int): The number of sublists to split the list into.

    Returns:
        generator: A generator expression containing n roughly equal-sized sublists.
    """
    k, m = divmod(len(lst), n)
    return (lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def chunker(seq, size):
    """
    Splits a sequence into chunks of a given size.

    Args:
        seq (sequence): The sequence to be chunked.
        size (int): The size of each chunk.

    Returns:
        generator: A generator expression containing the chunks of the sequence.
    """
    seq = list(seq)
    return (seq[pos: pos + size] for pos in range(0, len(seq), size))
