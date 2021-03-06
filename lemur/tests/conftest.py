import os
import pytest

from lemur import create_app
from lemur.database import db as _db
from lemur.auth.service import create_token

from .factories import AuthorityFactory, NotificationFactory, DestinationFactory, \
    CertificateFactory, UserFactory, RoleFactory, SourceFactory, EndpointFactory


def pytest_runtest_setup(item):
    if 'slow' in item.keywords and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")

    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed ({0})".format(previousfailed.name))


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


@pytest.yield_fixture(scope="session")
def app(request):
    """
    Creates a new Flask application for a test duration.
    Uses application factory `create_app`.
    """
    _app = create_app(os.path.dirname(os.path.realpath(__file__)) + '/conf.py')
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope="session")
def db(app, request):
    _db.drop_all()
    _db.create_all()

    _db.app = app

    UserFactory()
    r = RoleFactory(name='admin')
    UserFactory(roles=[r])

    _db.session.commit()
    yield _db
    _db.drop_all()


@pytest.yield_fixture(scope="function")
def session(db, request):
    """
    Creates a new database session with (with working transaction)
    for test duration.
    """
    db.session.begin_nested()
    yield db.session
    db.session.rollback()


@pytest.yield_fixture(scope="function")
def client(app, session, client):
    yield client


@pytest.fixture
def authority(session):
    a = AuthorityFactory()
    session.commit()
    return a


@pytest.fixture
def destination(session):
    d = DestinationFactory()
    session.commit()
    return d


@pytest.fixture
def source(session):
    s = SourceFactory()
    session.commit()
    return s


@pytest.fixture
def notification(session):
    n = NotificationFactory()
    session.commit()
    return n


@pytest.fixture
def certificate(session):
    u = UserFactory()
    a = AuthorityFactory()
    c = CertificateFactory(user=u, authority=a)
    session.commit()
    return c


@pytest.fixture
def endpoint(session):
    s = SourceFactory()
    e = EndpointFactory(source=s)
    session.commit()
    return e


@pytest.fixture
def role(session):
    r = RoleFactory()
    session.commit()
    return r


@pytest.fixture
def user(session):
    u = UserFactory()
    session.commit()
    user_token = create_token(u)
    token = {'Authorization': 'Basic ' + user_token}
    return {'user': u, 'token': token}


@pytest.fixture
def admin_user(session):
    u = UserFactory()
    admin_role = RoleFactory(name='admin')
    u.roles.append(admin_role)
    session.commit()
    user_token = create_token(u)
    token = {'Authorization': 'Basic ' + user_token}
    return {'user': u, 'token': token}


@pytest.fixture
def issuer_plugin():
    from lemur.plugins.base import register
    from .plugins.issuer_plugin import TestIssuerPlugin
    register(TestIssuerPlugin)
    return TestIssuerPlugin


@pytest.fixture
def notification_plugin():
    from lemur.plugins.base import register
    from .plugins.notification_plugin import TestNotificationPlugin
    register(TestNotificationPlugin)
    return TestNotificationPlugin


@pytest.fixture
def destination_plugin():
    from lemur.plugins.base import register
    from .plugins.destination_plugin import TestDestinationPlugin
    register(TestDestinationPlugin)
    return TestDestinationPlugin


@pytest.fixture
def source_plugin():
    from lemur.plugins.base import register
    from .plugins.source_plugin import TestSourcePlugin
    register(TestSourcePlugin)
    return TestSourcePlugin
