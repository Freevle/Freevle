import re
from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.properties import RelationshipProperty

from freevle import db
from freevle.utils.database import validate_slug
from freevle.utils.decorators import permalink
from freevle.utils.functions import camel_to_underscore

from .constants import *

from ..user.constants import POLYMORPHIC_IDENTITIES, USER_TYPE_LENGTH
from ..user.models import Admin

from ..news.models import NewsItem

page_group_view = db.Table('page_group_view',
    db.Column('page_id', db.Integer, db.ForeignKey('page.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

page_group_edit = db.Table('page_group_edit',
    db.Column('page_id', db.Integer, db.ForeignKey('page.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(CATEGORY_TITLE_LENGTH), nullable=False)
    slug = db.Column(db.String(CATEGORY_SLUG_LENGTH), nullable=False, unique=True)

    validate_slug = db.validates('slug')(validate_slug)

    @permalink
    def get_url(self):
        return 'cms.category_view', {'category_slug': self.slug}

class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(SUBCATEGORY_TITLE_LENGTH), nullable=False)
    slug = db.Column(db.String(SUBCATEGORY_SLUG_LENGTH), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    user_type_view = db.Column(db.String(USER_TYPE_LENGTH))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('category_id', 'slug'),
    )

    category = db.relationship(
        Category,
        backref=db.backref(
            'subcategories',
            order_by='Subcategory.id',
            lazy='dynamic'
        )
    )

    # groups_view = db.relationship(Group,
    #                          secondary=page_group_view,
    #                          order_by=Group.id,
    #                          lazy='dynamic',
    #                          backref=db.backref('pages_view',
    #                                             order_by='Page.id',
    #                                             lazy='dynamic'))

    validate_slug = db.validates('slug')(validate_slug)

    @db.validates('color')
    def validate_hex_color(self, key, value):
        if re.match('^\#[a-fA-F0-9]{6}$', value):
            return value
        else:
            raise ValueError("This is an invalid color code. It must be a html "
                             "hex color code without alpha e.g. #000000")

    @db.validates('user_type_view')
    def validate_user_type_view(self, key, value):
        if value is not None:
            value = value.lower()
            if value in POLYMORPHIC_IDENTITIES:
                return value
            else:
                raise ValueError("user_type_view has to be one of the POLYMORPHIC_IDENTITIES"
                                 "of the user blueprint.")
        else:
            return value

    def can_view(self, user):
        if isinstance(user, Admin):
            return True
        # elif db.join(user.groups, self.groups_view).all():
        #     return True
        # for group in POLYMORPHIC_IDENTITIES:
        #     if group in self.groups_view.all() and \
        #        isinstance(user, eval(group.capitalize()):
        #         return True
        elif isinstance(user, eval(self.user_type_view.capitalize())):
            return True
        return False

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=False)
    title = db.Column(db.String(PAGE_TITLE_LENGTH), nullable=False)
    slug = db.Column(db.String(PAGE_SLUG_LENGTH), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_published = db.Column(db.Boolean, nullable=False)
    datetime_created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_edited = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('subcategory_id', 'slug'),
    )

    subcategory = db.relationship(
        Subcategory,
        backref=db.backref('pages',
            order_by='Page.id',
            lazy='dynamic'
        )
    )

    # groups_edit = db.relationship(
    #     Group,
    #     secondary=page_group_edit,
    #     order_by=Group.id,
    #     lazy='dynamic',
    #     backref=db.backref('pages_edit',
    #         order_by='Page.id',
    #         lazy='dynamic'
    #     )
    # )

    validate_slug = db.validates('slug')(validate_slug)

    @permalink
    def get_url(self):
        return 'cms.page_view', {'page_slug': self.slug,
                                 'subcategory_slug': self.subcategory.slug,
                                 'category_slug': self.subcategory.category.slug}

    @permalink
    def get_edit_url(self):
        return 'admin.cms_page_edit', {'page_slug': self.slug,
                                       'subcategory_slug': self.subcategory.slug,
                                       'category_slug': self.subcategory.category.slug}
    @permalink
    def get_delete_url(self):
        return 'admin.cms_page_delete', {'page_slug': self.slug,
                                         'subcategory_slug': self.subcategory.slug,
                                         'category_slug': self.subcategory.category.slug}

    @staticmethod
    def get_page(category_slug, subcategory_slug, page_slug):
        # TODO: find out if this could be put into one query.
        cat = Category.query.filter(Category.slug == category_slug).first_or_404()
        sub = Subcategory.query.filter(Subcategory.category == cat)\
              .filter(Subcategory.slug == subcategory_slug).first_or_404()
        return Page.query.filter(Page.subcategory == sub)\
               .filter(Page.slug == page_slug).first_or_404()

    def can_edit(self, user):
        if isinstance(user, Admin):
            return True
        # elif db.join(user.groups, self.groups_edit).all():
        #     return True
        # for group in POLYMORPHIC_IDENTITIES:
        #     if group in self.groups_edit.all() and \
        #        isinstance(user, eval(group.capitalize())):
        #         return True
        return False

    def __repr__(self):
        return '({}) {}/{}/{}'.format(self.id, self.subcategory.category.slug,
                                      self.subcategory.slug, self.slug)

class PageSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column('type', db.String(PAGE_SECTION_TYPE_LENGTH))
    title = db.Column(db.String(PAGE_SECTION_TITLE_LENGTH), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('page_id', 'order'),
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'base'
    }

    page = db.relationship(
        Page,
        backref=db.backref(
            'sections',
            order_by='PageSection.order',
            lazy='dynamic'
        )
    )

    def __repr__(self):
        return '({}) {}Section'.format(self.id, self.section_type.capitalize())

class TextSection(PageSection):
    __mapper_args__ = {'polymorphic_identity': 'text'}

    id = db.Column(db.Integer, db.ForeignKey('page_section.id'), primary_key=True)
    content = db.Column(db.Text, nullable=False)

    page = db.relationship(
        Page,
        backref=db.backref(
            'text_sections',
            order_by='TextSection.order',
            lazy='dynamic'
        )
    )

class ImageSection(PageSection):
    __mapper_args__ = {'polymorphic_identity': 'image'}
    id = db.Column(db.Integer, db.ForeignKey('page_section.id'), primary_key=True)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    image_path = db.Column(db.String(IMAGE_SECTION_PATH_LENGTH), nullable=False)

    page = db.relationship(
        Page,
        backref=db.backref(
            'image_sections',
            order_by='ImageSection.order',
            lazy='dynamic'
        )
    )

    @db.validates('featured')
    def validate_featured(self, key, value):
        if value:
            self.order = -1
        return value

    @db.validates('image_path')
    def validate_image_path(self, key, value):
        # Clean path
        # Validate this thing is a picture
        return value

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linked_models = [Page, Subcategory, Category, NewsItem]
    for cls in linked_models:
        low_name = camel_to_underscore(cls.__name__)
        foreignkey_code = "{name}_id = db.Column(db.Integer, db.ForeignKey('{name}.id'))"\
                          .format(name=low_name)
        relationship_code = """
{low_name} = db.relationship(
    {name},
    backref=db.backref(
        'links',
        order_by={name}.id,
        lazy='dynamic'
    )
)
        """.format(low_name=low_name, name=cls.__name__)
        exec(foreignkey_code)
        exec(relationship_code)

    def __init__(self, **kwargs):
        if len(k.items()) > 1:
            raise KeyError('Only one link allowed.')
        for k,v in kwargs:
            if isinstance(getattr(self, k), RelationshipProperty)\
               or isinstance(getattr(self, k), db.Column):
               setattr(self, k, v)
