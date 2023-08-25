import ac
import acsys
import os
import sys
from functools import reduce

sys.path.insert(0, os.path.dirname(__file__) + "/stdlib64")
os.environ['PATH'] += ";."
from sim_info import info

MAX_TEMP = 105
MIN_TEMP = 65
MAX_PRES = 27
MIN_PRES = 25

timer_5 = 0
timer_10 = 0
blink = False
last = 0

window = 0
l_tyres = []
l_tower = []
l_gear = 0
l_speed = 0
l_delta = 0
l_rpms = 0
l_time = 0
l_fuel = []
l_bbal = 0
l_kers = 0

fuel_laps = 0
fuel_curr = 0
fuel_init = 0
fuel_last = 0

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

def getCarPosition(carId):
	if info.graphics.session == 2:
		return ac.getCarRealTimeLeaderboardPosition(carId) + 1
	else:
		return ac.getCarLeaderboardPosition(carId)

def parabola(x, w, h):
	return h * ((2*x/w - 1)**2 - 1)

def acMain(ac_version):
	global window, l_tyres, l_tower, l_gear, l_speed, l_delta, l_drs, l_rpms, l_time, l_best, l_fuel, l_bbal, l_kers

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

	l_gear = ac.addLabel(window, "N")
	ac.setPosition(l_gear, 350, 6)
	ac.setFontAlignment(l_gear, "center")
	ac.setCustomFont(l_gear, font_name, 0, 0)
	ac.setFontSize(l_gear, 48)

	l_speed = ac.addLabel(window, "123")
	ac.setPosition(l_speed, 305, 29)
	ac.setFontAlignment(l_speed, "right")
	ac.setCustomFont(l_speed, font_name, 0, 0)
	ac.setFontSize(l_speed, 26)

	l_delta = ac.addLabel(window, "-1.23")
	ac.setPosition(l_delta, 395, 38)
	ac.setFontAlignment(l_delta, "left")
	ac.setCustomFont(l_delta, font_name, 0, 0)
	ac.setFontSize(l_delta, 16)

	l_drs = ac.addLabel(window, "DRS")
	ac.setPosition(l_drs, 350, 5)
	ac.setFontAlignment(l_drs, "center")
	ac.setCustomFont(l_drs, font_name, 0, 0)
	ac.setFontSize(l_drs, 12)

	l_rpms = ac.addLabel(window, "1234")
	ac.setPosition(l_rpms, 350, 62)
	ac.setFontAlignment(l_rpms, "center")
	ac.setCustomFont(l_rpms, font_name, 0, 0)
	ac.setFontSize(l_rpms, 12)

	l_bbal = ac.addLabel(window, "BBal 12.3")
	ac.setPosition(l_bbal, 274, 89)
	ac.setFontAlignment(l_bbal, "center")
	ac.setCustomFont(l_bbal, font_name, 0, 0)
	ac.setFontSize(l_bbal, 14)

	l_kers = ac.addLabel(window, "SoC 12 Lap 34")
	ac.setPosition(l_kers, 274, 124)
	ac.setFontAlignment(l_kers, "center")
	ac.setCustomFont(l_kers, font_name, 0, 0)
	ac.setFontSize(l_kers, 14)

	l_time = ac.addLabel(window, "Last 1:23.456")
	ac.setPosition(l_time, 426, 89)
	ac.setFontAlignment(l_time, "center")
	ac.setCustomFont(l_time, font_name, 0, 0)
	ac.setFontSize(l_time, 14)

	l_best = ac.addLabel(window, "Best 1:23.456")
	ac.setPosition(l_best, 426, 124)
	ac.setFontAlignment(l_best, "center")
	ac.setCustomFont(l_best, font_name, 0, 0)
	ac.setFontSize(l_best, 14)

	for i in range(8):
		l_fuel.append(ac.addLabel(window, "12.3"))
		ac.setPosition(l_fuel[i], 30 + i%2*50, 37 + i//2*27)
		ac.setFontAlignment(l_fuel[i], "center")
		ac.setCustomFont(l_fuel[i], font_name, 0, 0)
		ac.setFontSize(l_fuel[i], 14 - 4 * (i//2 - i//4*2))
	ac.setText(l_fuel[2], "Fuel")
	ac.setText(l_fuel[3], "Last")
	ac.setText(l_fuel[6], "Laps")
	ac.setText(l_fuel[7], "Avg")

	for i in range(12):
		l_tyres.append(ac.addLabel(window, "123"))
		ac.setPosition(l_tyres[i], 138 + i%2*34, 28	 + i//2*18 + i//6*7)
		ac.setFontAlignment(l_tyres[i], "center")
		ac.setCustomFont(l_tyres[i], font_name, 0, 0)
		ac.setFontSize(l_tyres[i], 14)

	for i in range(5):
		l_tower.append(ac.addLabel(window, "driver"))
		ac.setPosition(l_tower[i], 602, 31 + i*23)
		ac.setFontAlignment(l_tower[i], "center")
		ac.setCustomFont(l_tower[i], font_name, 0, 0)
		ac.setFontSize(l_tower[i], 14)

	return "Dashboard"

def acUpdate(deltaT):
	global timer_5, timer_10, blink, last
	global window, l_tyres, l_tower, l_gear, l_speed, l_delta, l_drs, l_rpms, l_time, l_best, l_fuel, l_bbal, l_kers
	global fuel_laps, fuel_curr, fuel_init, fuel_last

	ac.setBackgroundOpacity(window, 0)

	timer_5 += deltaT
	if timer_5 >= 0.2:
		timer_5 = 0
		blink = not blink

	timer_10 += deltaT
	if timer_10 >= 0.1:
		timer_10 = 0

		# gear
		if blink and info.static.maxRpm - info.physics.rpms < 25:
			ac.setFontColor(l_gear, 1, 0, 0, 1)
		else:
			ac.setFontColor(l_gear, 1, 1, 1, 1)
		if info.physics.gear == 0:
			ac.setText(l_gear, "R")
		elif info.physics.gear == 1:
			ac.setText(l_gear, "N")
		else:
			ac.setText(l_gear, str(info.physics.gear - 1))

		# speed
		ac.setText(l_speed, "{:.0f}".format(info.physics.speedKmh))

		# delta
		ac.setText(l_delta, "{:+.2f}".format(ac.getCarState(0, acsys.CS.PerformanceMeter)))
		if ac.getCarState(0, acsys.CS.PerformanceMeter) < 0:
			ac.setFontColor(l_delta, 0, 1, 0, 1)
		else:
			ac.setFontColor(l_delta, 1, 1, 1, 1)

		# drs
		if info.static.hasDRS:
			if info.physics.drsEnabled:
				ac.setFontColor(l_drs, 0, 1, 0, 1)
			else:
				ac.setFontColor(l_drs, 0, 0, 0, 0.5)
		else:
			ac.setFontColor(l_drs, 0, 0, 0, 0)

		# rpms
		if info.physics.speedKmh < 2:
			ac.setText(l_rpms, str(info.physics.rpms))
		else:
			ac.setText(l_rpms, "")

		# brakes
		ac.setText(l_bbal, "BBal {:.1f}".format(info.physics.brakeBias * 100))

		# kers
		if info.static.hasERS or info.static.hasKERS:
			soc = 100 * info.physics.kersCharge
			if info.static.ersMaxJ:
				dep = 100 * (1 - info.physics.kersCurrentKJ / info.static.ersMaxJ * 1000)
				ac.setText(l_kers, "SoC {:00.0f} Lap {:00.0f}".format(soc*0.99, dep*0.99))
			elif info.static.kersMaxJ:
				dep = 100 * (1 - info.physics.kersCurrentKJ / info.static.kersMaxJ * 1000)
				ac.setText(l_kers, "SoC {:00.0f} Lap {:00.0f}".format(soc*0.99, dep*0.99))
			else:
				ac.setText(l_kers, "SoC {:00.0f}".format(soc*0.99))
		else:
			ac.setText(l_kers, "{:.0f}mm {:.0f}mm".format(*map(lambda x: x*1000, info.physics.rideHeight)))

		# laptime
		ac.setText(l_time, "Last " + info.graphics.lastTime)
		ac.setText(l_best, "Best " + info.graphics.bestTime)

		# fuel
		ac.setText(l_fuel[0], "{:.1f}".format(info.physics.fuel))
		if info.graphics.currentTime == "-:--:---":
			fuel_laps = 0
		if ac.isCarInPitline(0):
			fuel_laps = 0
		if last != ac.getCarState(0, acsys.CS.LapCount):
			last = ac.getCarState(0, acsys.CS.LapCount)
			if not ac.isCarInPitline(0):
				if fuel_laps == 0:
					fuel_init = info.physics.fuel
				else:
					fuel_last = fuel_curr if (fuel_laps > 1) else fuel_init
					fuel_curr = info.physics.fuel
				fuel_laps += 1
			ac.console(str(info.physics.fuel))
		if fuel_laps > 1:
			avg = (fuel_init - fuel_curr) / (fuel_laps - 1)
			est = info.physics.fuel / avg
			if est < 3:
				for i in range(len(l_fuel)):
					ac.setFontColor(l_fuel[i], 1, 0, 0, 1)
			ac.setText(l_fuel[1], "{:.2f}".format(fuel_last - fuel_curr))
			ac.setText(l_fuel[4], "{:.1f}".format(est))
			ac.setText(l_fuel[5], "{:.2f}".format(avg))
		else:
			for i in range(len(l_fuel)):
				ac.setFontColor(l_fuel[i], 1, 1, 1, 1)
			ac.setText(l_fuel[1], "-")
			ac.setText(l_fuel[4], "-")
			ac.setText(l_fuel[5], "-")

		# tyres
		for i in range(4):
			index = i//2*6 + i%2
			temp =  info.physics.tyreTempI[i]
			temp += info.physics.tyreTempM[i]
			temp += info.physics.tyreTempO[i]
			temp /= 3
			ac.setText(l_tyres[index], "{:.0f}".format(temp))
			ac.setFontColor(l_tyres[index], *tempColor(temp))
			pres = info.physics.wheelsPressure[i]
			ac.setText(l_tyres[index + 2], "{:.0f}".format(pres))
			ac.setFontColor(l_tyres[index + 2], *presColor(pres))
			wear = 1000 - info.physics.tyreWear[i] * 10
			ac.setText(l_tyres[index + 4], "{:.0f}‰".format(wear))
			ac.setFontColor(l_tyres[index + 4], *wearColor(wear))

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
		for i in range(len(l_tower)):
			c = cars[(me - i + 2) % cars_count]["id"]
			if i != len(l_tower)//2 and c == 0:
				ac.setText(l_tower[i], "")
			else:
				d_dist = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
				d_dist -= ac.getCarState(c, acsys.CS.NormalizedSplinePosition)
				d_laps = ac.getCarState(0, acsys.CS.LapCount)
				d_laps -= ac.getCarState(c, acsys.CS.LapCount)
				if i < len(l_tower)//2 and d_dist > 0:
					d_dist -= 1.0
					d_laps += 1
				if i > len(l_tower)//2 and d_dist < 0:
					d_dist += 1.0
					d_laps -= 1
				if info.graphics.session == 2:
					if d_laps < 0:
						ac.setFontColor(l_tower[i], 1, 1, 0, 1)
					elif d_laps > 0:
						ac.setFontColor(l_tower[i], 0, 1, 1, 1)
					else:
						ac.setFontColor(l_tower[i], 1, 1, 1, 1)
				if i == len(l_tower)//2:
					distance = "   L{:2d}".format(ac.getCarState(c, acsys.CS.LapCount) + 1)
				else:
					distance = "{:+6.0f}".format(d_dist * info.static.trackSPlineLength)
				name = list(map(lambda x: x.capitalize(), ac.getDriverName(c).split(" ")))
				ac.setText(l_tower[i], "{:3.3s}{:6.6s} {:4.4s}{}".format(
					str(getCarPosition(c)) + ".",
					reduce(lambda x, y: x + y[0], name, "") + name[-1][1:].lower(),
					"PIT" if ac.isCarInPitline(c) else "(" + ac.getCarTyreCompound(c) + ")",
					distance
				))

def onFormRender(deltaT):
	# rpms
	if info.static.maxRpm - info.physics.rpms < 250:
		ac.glColor4f(1, 0, 0, 1)
	else:
		ac.glColor4f(1, 1, 1, 1)
	p_w = 294
	s_w = 18
	gap = 3
	for i in range(p_w//(s_w+gap)):
		rpmPercent = i / (p_w // (s_w+gap))
		minPercent = 0.67
		if info.physics.rpms > info.static.maxRpm*(minPercent + (1 - minPercent)*rpmPercent):
			x = i*(gap + s_w) + gap/2
			ac.glBegin(3)
			ac.glVertex2f(203 + x,       32.5 + parabola(x,       p_w, 30.5))       # TL
			ac.glVertex2f(203 + x,       32.5 + parabola(x,       p_w, 30.5) + 2) # BL
			ac.glVertex2f(203 + x + s_w, 32.5 + parabola(x + s_w, p_w, 30.5) + 2) # BR
			ac.glVertex2f(203 + x + s_w, 32.5 + parabola(x + s_w, p_w, 30.5))       # TR
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
