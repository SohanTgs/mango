from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.conf import settings

from utils.helpers import *
from general.models import Setting, Seo
from general.forms import SettingForm

from django.core.cache import cache

from django.core.files.storage import FileSystemStorage
import json
import django.conf as conf

from django.templatetags.static import static
from django.core.files import File

from django.core.mail import BadHeaderError, send_mail
from django.core.mail import EmailMultiAlternatives
from django.http import Http404

import vonage
from django.core.management import call_command


@login_required(login_url='admin:login')
def index(request):

	contents = {
		'pageTitle':'Dashboard'
	}

	return render(request, 'admin/index.html', contents)
	
@login_required(login_url='admin:login')
def generalSetting(request):

	pageTitle = 'General Setting'

	if(request.method == 'POST'):

		form = SettingForm(request.POST) 

		if form.is_valid(): 
			general = Setting.objects.first()
			general.site_name = request.POST['site_name']
			general.cur_text = request.POST['cur_text']
			general.cur_sym = request.POST['cur_sym']
			general.base_color = request.POST['base_color']

			# request.POST.get('secure_password', 0)
			general.g_translate = 'google' in request.POST or 0
			general.agree_policy = 'agree' in request.POST or 0
			general.registration = 'registration' in request.POST or 0
			general.force_ssl = 'force_ssl' in request.POST or 0

			general.save()

			messages.success(request, 'General info updatd successfully')
			return Back(request)
		else:
			
			form = SettingForm(request.POST)
			contents = {
				'pageTitle': pageTitle,
				'form': form
			}
			
			return render(request, 'admin/setting/general.html', contents)

	else: 

		contents = {
			'pageTitle': pageTitle
		}

		return render(request, 'admin/setting/general.html', contents)

@login_required(login_url='admin:login')
def clearCache(request):

	cache.clear()
	messages.success(request, 'Cache clear successfully')
	return Back(request)

@login_required(login_url='admin:login')
def logo(request):

	if(request.method == 'POST'): 
		general = Setting.objects.first()

		if( bool(request.FILES.get('logo', False)) == True):
			general.logo = request.FILES.get('logo')
 
		if( bool(request.FILES.get('favicon', False)) == True):
			general.favicon = request.FILES.get('favicon')

		general.save()

		messages.success(request, 'Image updated successfully')
		return Back(request)

	else:

		contents = {
			'pageTitle':'Logo and Favicon'
		}

		return render(request, 'admin/setting/logo_icon.html', contents)


@login_required(login_url='admin:login')
def seo(request):

	if(request.method == 'POST'): 

		seo = Seo.objects.first()

		seo.keyword = json.dumps(request.POST.getlist('keywords[]'))
		seo.description = request.POST['description']

		if( bool(request.FILES.get('image', False)) == True):
			seo.image = request.FILES.get('image')

		seo.save()

		messages.success(request, 'SEO info updated successfully')
		return Back(request)

	else:	

		seo = Seo.objects.first()
		contents = {
			'pageTitle':'SEO',
			'seo':Seo.objects.first()
		}
		 
		return render(request, 'admin/setting/seo.html', contents)
	

@login_required(login_url='admin:login')
def customAsset(request):

	if(request.method == 'POST'): 

		# Read in the file
		# with open('static/frontend/css/custom.css', 'w') as file :
		# 	filedata = file.write('')

		# Write the file out again
		with open('static/frontend/css/custom.css', 'w') as file:
			file.write(request.POST['css'])

		with open('static/frontend/css/custom.css', 'r+') as fd:
		    lines = fd.readlines()
		    fd.seek(0)
		    fd.writelines(line for line in lines if line.strip())
		    fd.truncate()

		# css = open('static/frontend/css/custom.css', 'w')
		# cssFile = File(css)
		# cssFile.write(request.POST['css'])
		# cssFile.close()
		# css.close()

		messages.success(request, 'Custom asset successfully')
		return Back(request)

	else: 

		css = open('static/frontend/css/custom.css', 'r')

		# if f.mode == 'r':
		file = css.read()

		contents = {
			'pageTitle':'Custom Assets',
			'css':file
		}

		return render(request, 'admin/setting/custom_asset.html', contents)	
		# url = static('frontend/css/custom.css')


@login_required(login_url='admin:login')
def emailConfigure(request):

	if(request.method == 'POST'): 

		method = request.POST['email_method']
		
		if(method == 'smtp'):
			data = {
				"name": "smtp",
				"EMAIL_HOST": request.POST['host'],
				"EMAIL_PORT": request.POST['port'],
				"EMAIL_USE_TLS": request.POST['enc'] == 'tls' or False,
				"EMAIL_USE_SSL": request.POST['enc'] == 'ssl' or False,
				"EMAIL_HOST_USER": request.POST['username'],
				"EMAIL_HOST_PASSWORD": request.POST['password']
			}

			general = Setting.objects.first()
			general.mail_config = json.dumps(data)
			general.save()

		messages.success(request, 'Email configuration has been updated')
		return Back(request)

	else: 

		contents = {
			'pageTitle':'Email Configuration'
		}

		return render(request, 'admin/email_template/configure.html', contents)	


@login_required(login_url='admin:login')
def sendTestMail(request):

	if(request.method == 'POST'): 

		email = request.POST['email']

		if(email == ''):
			messages.error(request, 'Email field is required')
			return Back(request)

		try:
			general = Setting.objects.first()

			# for key, value in json.loads(general.mail_config).items():

			# 	if(key == 'EMAIL_USE_TLS'):
			# 		conf.settings.EMAIL_USE_TLS = value

			# 	if(key == 'EMAIL_USE_SSL'):
			# 		conf.settings.EMAIL_USE_SSL = value

			# 	if(key == 'EMAIL_HOST'):
			# 		conf.settings.EMAIL_HOST = value

			# 	if(key == 'EMAIL_HOST_USER'):
			# 		conf.settings.EMAIL_HOST_USER = value

			# 	if(key == 'EMAIL_HOST_PASSWORD'):
			# 		conf.settings.EMAIL_HOST_PASSWORD = value

			# 	if(key == 'EMAIL_PORT'):
			# 		conf.settings.EMAIL_PORT = value	

			send_mail(
				'This is demo mail for testing',
				'',
				general.email_from, 
				[email],
				html_message=general.email_template.replace('{{username}}', email),
				fail_silently=False,
			)

		# except BadHeaderError:
		except Exception as error:
			messages.error(request, error)
			return Back(request)
			# raise Http404

		messages.success(request, 'You should receive a test mail at ' + email + ' shortly')
		return Back(request)

	else: 
		messages.error(request, 'Sorry, Invalid request')
		return Back(request)


@login_required(login_url='admin:login')
def mailSetting(request):

	if(request.method == 'POST'): 
		
		general = Setting.objects.first()
		general.email_from = request.POST['email_from']
		general.email_template = request.POST['email_template']
		general.save()

		messages.success(request, 'Global Email Template has been updated')
		return Back(request)

	else: 

		contents = {
			'pageTitle':'Global Email Setting'
		}

	return render(request, 'admin/email_template/global.html', contents)	


@login_required(login_url='admin:login')
def smsSetting(request):

	if(request.method == 'POST'): 

		general = Setting.objects.first()
		general.sms_api = request.POST['sms_api']
		general.save()

		messages.success(request, 'Global Sms Template has been updated')
		return Back(request)

	else: 

		contents = {
			'pageTitle':'Global Sms Setting'
		}

	return render(request, 'admin/sms_template/global.html', contents)


@login_required(login_url='admin:login')
def smsConfigure(request):
	
	if(request.method == 'POST'): 
		
		data = {
			"sms_method": request.POST['sms_method'],
			"nexmo_api_key": request.POST['nexmo_api_key'],
			"nexmo_api_secret": request.POST['nexmo_api_secret'],
		}

		general = Setting.objects.first()
		general.sms_config = json.dumps(data)
		general.save()

		messages.success(request, 'Sms configuration has been updated')
		return Back(request)

	else: 

		contents = {
			'pageTitle':'Sms Configuration'
		}

	return render(request, 'admin/sms_template/configure.html', contents)	


@login_required(login_url='admin:login')
def sendTestSms(request):

	if(request.method == 'POST'): 

		mobile = request.POST['mobile']

		if(mobile == ''):
			messages.error(request, 'Mobile field is required')
			return Back(request)

		try:

			general = Setting.objects.first()
			config = json.loads(general.sms_config)

			client = vonage.Client(key=config.get('nexmo_api_key'), secret=config.get('nexmo_api_secret'))
			sms = vonage.Sms(client)

			responseData = sms.send_message(
			    {
			        "from": general.site_name,
			        "to": mobile,
			        "text": "A text message sent using the Nexmo SMS API from "+general.site_name,
			    }
			)

			if responseData["messages"][0]["status"] == "0":
				messages.success(request, 'You should receive a test sms at ' + mobile + ' shortly')
				return Back(request)

			else:
				messages.error(request, f"Message failed with error: {responseData['messages'][0]['error-text']}")
				return Back(request)

		except Exception as error:
			messages.error(request, error)
			return Back(request)

	else: 
		messages.error(request, 'Sorry, Invalid request')
		return Back(request)


@login_required(login_url='admin:login')
def screenRecord(request):

	contents = {
		'pageTitle':'Screen Record'
	}

	return render(request, 'admin/setting/screen_record.html', contents)





