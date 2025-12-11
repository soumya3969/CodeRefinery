def bad_function(items, results=[]):
    for i in items:
        if i>10:
            if i>20:
                if i>30:
                    results.append(i*2)
                else:
                    results.append(i)
            else:
                results.append(i/2)
        else:
            results.append(0)
    return results

def unsafe_eval(user_input):
    return eval(user_input)