from email.utils import format_datetime
from rfeed import Feed, Item, Extension, Guid, Serializable
from .utils import slugify
from ....shared.security import sign_feed_item, load_public_key_pem


class AtomLinkNamespace(Extension):
    def get_namespace(self):
        return {"xmlns:atom": "http://www.w3.org/2005/Atom"}


class AtomLink(Serializable):
    def __init__(self, href):
        Serializable.__init__(self)
        self.href = href

    def publish(self, handler):
        Serializable.publish(self, handler)
        self._write_element("atom:link", None, {"href": self.href, "rel": "self"})


class Signature(Serializable):
    """
    Custom tag for adding a signature to an RSS item.
    """

    def __init__(self, signature_value, key_id):
        Serializable.__init__(self)
        self.signature_value = signature_value
        self.key_id = key_id

    def publish(self, handler):
        Serializable.publish(self, handler)
        self._write_element(
            "signature",
            self.signature_value,
            {"keyId": self.key_id},
        )


def generate_rss(
    title, link, description, author, language, build_date, items, sign=None
):

    feed_items = []
    for item in items:
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
        id = item.get("id") or slugify(item["path"])
        pub_date = item["date"]
        description = item.get("content")
        title = item.get("title")

        if sign:
            signature_value = (
                sign_feed_item(sign["key"], pub_date, title, description)
                if sign["key"]
                else None
            )
            signature_id = sign["id"] if sign["id"] else None

        feed_items.append(
            Item(
                title=title,
                link=item.get("link") or f"{link}/feed/{id}",
                description=description,
                author=f"{author['name']} ({author['email']})",
                guid=Guid(id),
                pubDate=pub_date,
                extensions=[
                    (
                        Signature(signature_value, sign["id"])
                        if signature_value and signature_id
                        else None
                    )
                ],
            )
        )
    feed = Feed(
        title=title,
        link=link,
        description=description,
        language=language,
        lastBuildDate=build_date,
        items=feed_items,
        extensions=[AtomLinkNamespace(), AtomLink(link)],
    )

    return feed.rss()
