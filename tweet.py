
def reply(root_tweet, parent_id, reply_tweet):
    if root_tweet['id'] == parent_id:
        root_tweet.setdefault('replies', [])
        root_tweet['replies'].append(reply_tweet)
        return

    tweet = get(root_tweet['replies'], parent_id)
    #print('reply', tweet)
    tweet.setdefault('replies', [])
    tweet['replies'].append(reply_tweet)


def get(replies, reply_id):
    for reply in replies:
        #print('reply', reply)
        if reply['id'] == reply_id:
            return reply
    for reply in replies:
        r = get(reply.get('replies', []), reply_id)
        if r:
            return r


if __name__ == '__main__':
    t = {'id': '1', 'replies': [ {'id':'11', 'replies':[ {'id':'111', 'replies':[]} ]} ]}
    #print(t)

    #print(get(t, '1'))
    print(get(t['replies'], '11'))
    print(get(t['replies'], '111'))

    reply(t, '1', {'id':'12'})
    print(t)

    reply(t, '12', {'id':'121'})
    print(t)

    reply(t, '111', {'id':'1112'})
    print(t)

