import ac
import acsys
import os
import sys
sys.path.insert(0, os.path.dirname(__file__) + "/stdlib64")
os.environ['PATH'] += ";."
from sim_info import info
from functools import reduce

MAX_TEMP = 105
MIN_TEMP = 65
MAX_PRES = 27
MIN_PRES = 25
MAX_RPMS = 0

def maxRpm():
	if MAX_RPMS:
		return MAX_RPMS
	else:
		return info.static.maxRpm

def tempColor(t):
	if t > MAX_TEMP:
		return [1, 1, 0, 1]
	elif t < MIN_TEMP:
		return [0, 1, 1, 1]
	else:
		return [1, 1, 1, 1]

def presColor(p):
	if p > MAX_PRES:
		return [1, 1, 0, 1]
	elif p < MIN_PRES:
		return [0, 1, 1, 1]
	else:
		return [1, 1, 1, 1]

def wearColor(w):
	if w > 10:
		return [1, 1, 0, 1]
	else:
		return [1, 1, 1, 1]

def parabola(x, w, h):
	return h * ((2*x/w - 1)**2 - 1)

window = 0
labels = {}

timer_update = 0
blink = False
timer_blink = 0
last = 0
line = False
timer_line = 60

fuel_laps = 0
fuel_curr = 0
fuel_init = 0
fuel_last = 0
fuel_mean = 0
kers_curr = 100
kers_last = 0

def acMain(ac_version):
	global window, labels

	window = ac.newApp("Dashboard")
	ac.setSize(window, 700, 150)
	ac.setTitle(window, "")
	ac.setIconPosition(window, -9999, -9999)
	ac.drawBorder(window, 0)
	ac.setBackgroundTexture(window, "apps/python/dashboard/bg.png")
	font_name = "Space Mono"
	ac.initFont(0, font_name, 0, 0)
	ac.initFont(0, font_name, 0, 0)
	ac.addRenderCallback(window, onFormRender)

	labels.update({'gear': ac.addLabel(window, "N")})
	ac.setPosition(labels['gear'], 350, 6)
	ac.setFontAlignment(labels['gear'], "center")
	ac.setCustomFont(labels['gear'], font_name, 0, 0)
	ac.setFontSize(labels['gear'], 48)

	labels.update({'speed': ac.addLabel(window, "123")})
	ac.setPosition(labels['speed'], 305, 29)
	ac.setFontAlignment(labels['speed'], "right")
	ac.setCustomFont(labels['speed'], font_name, 0, 0)
	ac.setFontSize(labels['speed'], 26)

	labels.update({'delta': ac.addLabel(window, "-1.23")})
	ac.setPosition(labels['delta'], 395, 38)
	ac.setFontAlignment(labels['delta'], "left")
	ac.setCustomFont(labels['delta'], font_name, 0, 0)
	ac.setFontSize(labels['delta'], 16)

	labels.update({'drs': ac.addLabel(window, "DRS")})
	ac.setPosition(labels['drs'], 350, 5)
	ac.setFontAlignment(labels['drs'], "center")
	ac.setCustomFont(labels['drs'], font_name, 0, 0)
	ac.setFontSize(labels['drs'], 12)

	labels.update({'rpms': ac.addLabel(window, "1234")})
	ac.setPosition(labels['rpms'], 350, 62)
	ac.setFontAlignment(labels['rpms'], "center")
	ac.setCustomFont(labels['rpms'], font_name, 0, 0)
	ac.setFontSize(labels['rpms'], 12)

	labels.update({'bbal': ac.addLabel(window, "BBal 12.3")})
	ac.setPosition(labels['bbal'], 274, 89)
	ac.setFontAlignment(labels['bbal'], "center")
	ac.setCustomFont(labels['bbal'], font_name, 0, 0)
	ac.setFontSize(labels['bbal'], 14)

	labels.update({'kers': ac.addLabel(window, "SoC 12 Lap 34")})
	ac.setPosition(labels['kers'], 274, 124)
	ac.setFontAlignment(labels['kers'], "center")
	ac.setCustomFont(labels['kers'], font_name, 0, 0)
	ac.setFontSize(labels['kers'], 14)

	labels.update({'time': ac.addLabel(window, "Last 1:23.456")})
	ac.setPosition(labels['time'], 426, 89)
	ac.setFontAlignment(labels['time'], "center")
	ac.setCustomFont(labels['time'], font_name, 0, 0)
	ac.setFontSize(labels['time'], 14)

	labels.update({'best': ac.addLabel(window, "Best 1:23.456")})
	ac.setPosition(labels['best'], 426, 124)
	ac.setFontAlignment(labels['best'], "center")
	ac.setCustomFont(labels['best'], font_name, 0, 0)
	ac.setFontSize(labels['best'], 14)

	labels.update({'fuel': []})
	for i in range(4):
		labels['fuel'].append(ac.addLabel(window, "12.34"))
		ac.setPosition(labels['fuel'][i], 55, 35 + i*28)
		ac.setFontAlignment(labels['fuel'][i], "center")
		ac.setCustomFont(labels['fuel'][i], font_name, 0, 0)
		ac.setFontSize(labels['fuel'][i], 14)

	labels.update({'tyres': []})
	for i in range(12):
		labels['tyres'].append(ac.addLabel(window, "123"))
		ac.setPosition(labels['tyres'][i], 138 + i%2*34, 28	 + i//2*18 + i//6*7)
		ac.setFontAlignment(labels['tyres'][i], "center")
		ac.setCustomFont(labels['tyres'][i], font_name, 0, 0)
		ac.setFontSize(labels['tyres'][i], 14)

	labels.update({'tower': []})
	for i in range(5):
		labels['tower'].append(ac.addLabel(window, "driver"))
		ac.setPosition(labels['tower'][i], 602, 31 + i*23)
		ac.setFontAlignment(labels['tower'][i], "center")
		ac.setCustomFont(labels['tower'][i], font_name, 0, 0)
		ac.setFontSize(labels['tower'][i], 14)

	return "Dashboard"

def acUpdate(deltaT):
	global window, labels
	global timer_blink, timer_update, timer_line, blink, last, line
	global fuel_laps, fuel_curr, fuel_init, fuel_last, fuel_mean, kers_curr, kers_last

	ac.setBackgroundOpacity(window, 0)

	timer_update += deltaT
	timer_blink += deltaT
	timer_line += deltaT
	if timer_update >= 0.1:
		timer_update = 0

		if timer_blink >= 0.5:
			blink = not blink
			timer_blink = 0

		if last != ac.getCarState(0, acsys.CS.LapCount):
			last = ac.getCarState(0, acsys.CS.LapCount)
			line = True
			timer_line = 0
		else:
			line = False

		# gear
		gear = info.physics.gear
		if gear == 0:
			ac.setText(labels['gear'], "R")
		elif gear == 1:
			ac.setText(labels['gear'], "N")
		else:
			ac.setText(labels['gear'], str(gear - 1))
		if maxRpm() - info.physics.rpms < 200:
			ac.setFontColor(labels['gear'], 1, 0, 0, 1)
		else:
			ac.setFontColor(labels['gear'], 1, 1, 1, 1)

		# speed
		ac.setText(labels['speed'], "{:.0f}".format(info.physics.speedKmh))

		# delta
		ac.setText(labels['delta'], "{:+.2f}".format(ac.getCarState(0, acsys.CS.PerformanceMeter)))
		if ac.getCarState(0, acsys.CS.PerformanceMeter) < 0:
			ac.setFontColor(labels['delta'], 0, 1, 0, 1)
		else:
			ac.setFontColor(labels['delta'], 1, 1, 1, 1)

		# drs
		if info.static.hasDRS:
			if info.physics.drsEnabled:
				ac.setFontColor(labels['drs'], 0, 1, 0, 1)
			else:
				ac.setFontColor(labels['drs'], 0, 0, 0, 0.5)
		else:
			ac.setFontColor(labels['drs'], 0, 0, 0, 0)

		# rpms
		if info.physics.speedKmh < 1:
			ac.setText(labels['rpms'], str(info.physics.rpms))
		else:
			ac.setText(labels['rpms'], "")

		# brakes
		ac.setText(labels['bbal'], "BBal {:.1f}%".format(info.physics.brakeBias * 100))

		# kers
		if info.static.hasERS or info.static.hasKERS:
			soc = 100 * info.physics.kersCharge
			dep = 100 * info.physics.kersCurrentKJ * 1000 / (info.static.ersMaxJ + info.static.kersMaxJ)
			if line:
				kers_last = kers_curr
				kers_curr = soc
			if timer_line > 5:
				ac.setText(labels['kers'], "SoC {:0.0f} Lap {:0.0f}".format(soc, 100 - dep))
				ac.setFontColor(labels['kers'], 1, 1, 1, 1)
			else:
				ac.setText(labels['kers'], "{:+.1f}%".format(kers_curr - kers_last))
				if kers_curr - kers_last < 0:
					ac.setFontColor(labels['kers'], 1, 0, 0, 1)
				else:
					ac.setFontColor(labels['kers'], 0, 1, 0, 1)
		else:
			ac.setText(labels['kers'], "ABS {:.0f} TC {:.0f}".format(100 * info.physics.abs, 100 * info.physics.tc))

		# laptime
		ac.setText(labels['time'], "Last " + info.graphics.lastTime)
		ac.setText(labels['best'], "Best " + info.graphics.bestTime)

		# fuel
		if ac.isCarInPitline(0) or info.graphics.currentTime == "-:--:---":
			fuel_laps = 0
		elif line:
			if fuel_laps == 0:
				fuel_init = info.physics.fuel
			else:
				fuel_last = fuel_curr if fuel_laps > 1 else fuel_init
				fuel_curr = info.physics.fuel
			fuel_laps += 1
		if fuel_laps > 1:
			fuel_mean = (fuel_init - fuel_curr) / (fuel_laps - 1)
		ac.setText(labels['fuel'][0], "{:.1f} L".format(info.physics.fuel))
		ac.setText(labels['fuel'][1], "Last {:.2f}".format(fuel_last - fuel_curr))
		ac.setText(labels['fuel'][2], "Mean {:.2f}".format(fuel_mean))
		ac.setText(labels['fuel'][3], "{:.1f} laps".format(info.physics.fuel / fuel_mean if fuel_mean else 0))
		if fuel_mean and blink and info.physics.fuel / fuel_mean < 3:
			for i in range(len(labels['fuel'])):
				ac.setFontColor(labels['fuel'][i], 1, 0, 0, 1)
		else:
			for i in range(len(labels['fuel'])):
				ac.setFontColor(labels['fuel'][i], 1, 1, 1, 1)

		# tyres
		for i in range(4):
			index = i//2*6 + i%2
			temp =  info.physics.tyreTempI[i]
			temp += info.physics.tyreTempM[i]
			temp += info.physics.tyreTempO[i]
			temp /= 3
			ac.setText(labels['tyres'][index], "{:.0f}".format(temp))
			ac.setFontColor(labels['tyres'][index], *tempColor(temp))
			pres = info.physics.wheelsPressure[i]
			ac.setText(labels['tyres'][index + 2], "{:.0f}".format(pres))
			ac.setFontColor(labels['tyres'][index + 2], *presColor(pres))
			wear = 1000 - info.physics.tyreWear[i] * 10
			ac.setText(labels['tyres'][index + 4], "{:.0f}‰".format(wear))
			ac.setFontColor(labels['tyres'][index + 4], *wearColor(wear))

		# traffic
		cars = []
		cars_count = ac.getCarsCount()
		for car_id in range(cars_count):
			cars.append(dict(
				id = car_id,
				dist = ac.getCarState(car_id, acsys.CS.NormalizedSplinePosition)
			))
		cars.sort(key = lambda car: car["dist"])
		me = 0
		for i in range(cars_count):
			if cars[i]["id"] == 0:
				me = i
		mid = len(labels['tower']) // 2 # highlighted tower position
		for i in range(len(labels['tower'])):
			c = cars[(me - i + mid) % cars_count]["id"]
			if i != mid and c == 0:
				ac.setText(labels['tower'][i], "")
			else:
				dist_delta = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
				dist_delta -= ac.getCarState(c, acsys.CS.NormalizedSplinePosition)
				laps_delta = ac.getCarState(0, acsys.CS.LapCount)
				laps_delta -= ac.getCarState(c, acsys.CS.LapCount)
				if i < mid and dist_delta > 0:
					dist_delta -= 1.0
					laps_delta += 1
				if i > mid and dist_delta < 0:
					dist_delta += 1.0
					laps_delta -= 1
				if info.graphics.session == 2:
					if laps_delta < 0:
						ac.setFontColor(labels['tower'][i], 1, 1, 0, 1)
					elif laps_delta > 0:
						ac.setFontColor(labels['tower'][i], 0, 1, 1, 1)
					else:
						ac.setFontColor(labels['tower'][i], 1, 1, 1, 1)
					pos = str(ac.getCarRealTimeLeaderboardPosition(c) + 1) + "."
				else:
					pos = str(ac.getCarLeaderboardPosition(c)) + "."
				name = list(ac.getDriverName(c).split(" "))
				name = reduce(lambda x, y: x + y[0], name, "") + name[-1][1:]
				if ac.isCarInPit(c):
					comp = "BOX"
				elif ac.isCarInPitline(c):
					comp = "PIT"
				else:
					comp = "(" + ac.getCarTyreCompound(c) + ")"
				if i == mid:
					dist = "  L{:2d}".format(ac.getCarState(c, acsys.CS.LapCount) + 1)
				else:
					dist = "{:+5.0f}".format(dist_delta * info.static.trackSPlineLength)
				ac.setText(labels['tower'][i], "{:3.3s}{:7.7s} {:4.4s}{}".format(pos, name, comp, dist))

def onFormRender(deltaT):
	# rpms
	if maxRpm() - info.physics.rpms < 400:
		ac.glColor4f(1, 0, 0, 1)
	else:
		ac.glColor4f(1, 1, 1, 1)
	p_w = 300
	s_w = 15
	gap = 1
	for i in range((p_w-gap)//(s_w+gap)):
		rpmPercent = i / ((p_w-gap)//(s_w+gap))
		minPercent = 0.67
		if info.physics.rpms > maxRpm() * (minPercent + (1 - minPercent)*rpmPercent):
			x = i*(gap + s_w) + gap + 6
			ac.glBegin(3)
			ac.glVertex2f(200 + x,       33 + parabola(x,       p_w, 31.5))     # TL
			ac.glVertex2f(200 + x,       33 + parabola(x,       p_w, 31.5) + 3) # BL
			ac.glVertex2f(200 + x + s_w, 33 + parabola(x + s_w, p_w, 31.5) + 3) # BR
			ac.glVertex2f(200 + x + s_w, 33 + parabola(x + s_w, p_w, 31.5))     # TR
			ac.glEnd()

	# drs
	if info.static.hasDRS and info.physics.drsAvailable:
		ac.glColor4f(0, 1, 0, 1)
		ac.glBegin(1)
		ac.glVertex2f(338, 8)
		ac.glVertex2f(338, 21)
		ac.glVertex2f(363, 21)
		ac.glVertex2f(363, 8)
		ac.glVertex2f(338, 8)
		ac.glEnd()

	# dirt
	for i in range(len(info.physics.tyreDirtyLevel)):
		dirt = (info.physics.tyreDirtyLevel[i] / 5) ** 0.33
		ac.glColor4f(1, 0, 0, 1)
		ac.glQuad(119 + i%2*69, 82 + i//2*61 - dirt*50, 3, dirt*50)
