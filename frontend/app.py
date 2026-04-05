import os
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Depends, Request, HTTPException
from starlette.config import Config
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import gradio as gr
from gradio_app_dup import build_gradio_app
app = FastAPI()
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")


# Replace these with your own OAuth settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = "..."

config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

SECRET_KEY = os.environ.get('SECRET_KEY') or "a_very_secret_key"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Dependency to get the current user
def get_user(request: Request):
    user = request.session.get('user')
    nda = request.session.get('nda_accepted', False)
    if user and nda:
        return user["name"]
    else:
        raise HTTPException(status_code=403, detail="NDA not accepted")


# @app.get('/')
# def public(user: dict = Depends(get_user)):
#     if user:
#         return RedirectResponse(url='/waferGPT')
#     else:
#         return RedirectResponse(url='/waferGPT-login')

@app.get("/")
def public(request: Request):
    user = request.session.get('user')
    nda = request.session.get('nda_accepted', False)

    if not user:
        return RedirectResponse(url="/waferGPT-login")
    elif not nda:
        return RedirectResponse(url="/nda")
    else:
        return RedirectResponse(url="/waferGPT")


@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get("/accept-nda")
async def accept_nda(request: Request):
    request.session["nda_accepted"] = True
    return RedirectResponse(url="/waferGPT")



@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    # If your app is running on https, you should ensure that the
    # `redirect_uri` is https, e.g. uncomment the following lines:
    #
    # from urllib.parse import urlparse, urlunparse
    # redirect_uri = urlunparse(urlparse(str(redirect_uri))._replace(scheme='https'))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/auth')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url='/')
    request.session['user'] = dict(access_token)["userinfo"]
    # request.session['username'] = dict(access_token)["userinfo"]["name"]
    request.session['nda_accepted'] = False  # Mark NDA as not accepted yet
    return RedirectResponse(url='/nda')

with gr.Blocks(title="WaferGPT") as login_demo:
    gr.Markdown("### Welcome to WaferGPT")
    gr.Markdown("Please login to access the wafer defect detection tools.")
    gr.Button("Login", link="/login")


def build_nda_screen():
    with gr.Blocks(title="NDA Agreement") as nda_demo:
        gr.Markdown("## Non-Disclosure Agreement")

        gr.HTML("""
            <iframe src="/static/NextAIworks Mutual NDA.pdf" width="100%" height="600px" style="border: 1px solid #ccc;">
            </iframe>
        """)

        gr.Button(" I Agree", link="/accept-nda")

    return nda_demo



nda_demo = build_nda_screen()
app = gr.mount_gradio_app(app, nda_demo, path="/nda")

app = gr.mount_gradio_app(app, login_demo, path="/waferGPT-login")

def greet(request: gr.Request):
    return f"Welcome to Gradio, {request.username}"

# with gr.Blocks() as main_demo:
#     m = gr.Markdown("Welcome to Gradio!")
#     gr.Button("Logout", link="/logout")
#     main_demo.load(greet, None, m)


main_demo = build_gradio_app()

app = gr.mount_gradio_app(app, main_demo, path="/waferGPT", auth_dependency=get_user)

if __name__ == '__main__':
    uvicorn.run(app,host="0.0.0.0", port=8501)