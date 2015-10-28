#!python3
#written by pbsds / Peder Bergebakken Sundt
import sfml as sf#pysfml 1.3
if not hasattr(sf, "RenderWindow"):
	from sfml import sf#2.2.0
from copy import deepcopy
import time

def MakeBoard():
	board = [[None for _ in range(8)] for _ in range(8)]
	for i in range(8):
		board[i][1] = "bpawn"
		board[i][6] = "wpawn"
	for e, i in enumerate(("tower", "knight", "bishop", "queen")):
		board[e][0] = "b"+i
		board[7-e][0] = "b"+i
		board[e][7] = "w"+i
		board[7-e][7] = "w"+i
	board[4][0] = "bking"
	board[4][7] = "wking"
	return board

def GetLegalMoves(board, player, pos = None, offensive=False, doKingCheck=True):#set pos to a pice to get it's possible movements. offensive lets pieces attack their own. used to check if the king is in danger
	out = []
	if player.Selected or pos:
		x, y = pos if pos else player.Selected
		curr = board[x][y][1:]#current piece
		color = board[x][y][0]
		white = (color=="w")*1
		enemy = "wb"[white]
		
		if curr == "pawn" and 0<y<7:
			if not board[x][y+1-2*white]:#not blocked
				out.append((x, y+1-2*white))#step forward
				
				if y==1+5*white and not board[x][y+2-4*white]:#first move gets double
					out.append((x, y+2-4*white))
			
			for i in (-1, +1):
				if 0<=x+i<8:
					if board[x+i][y+1-2*white]:
						if board[x+i][y+1-2*white][0]==enemy:
							out.append((x+i, y+1-2*white))
					elif offensive:
						out.append((x+i, y+1-2*white))
		elif curr == "king":
			for cx in (x-1, x, x+1):
				for cy in (y-1, y, y+1):
					if cx==x and cy==y: continue
					if 0<=cx<8 and 0<=cy<8:
						dest = board[cx][cy]
						if dest and dest[0]==color: continue
						
						free = True
						for ex in range(8):
							for ey in range(8):
								if board[ex][ey] and board[ex][ey][0] != color:#for each enemy on the board:
									if board[ex][ey][1:] == "king":#to avoid infinite recursion
										if abs(cx-ex) <= 1 and abs(cy-ey) <= 1:
											free = False#literally never happens, but it can still handle the situation
											break
									elif (cx, cy) in GetLegalMoves(board, player, (ex, ey), offensive=True):#check if king's destination is in isght of an another piece
										free = False
										break
							if not free: break		
						
						if free:
							out.append((cx, cy))
		elif curr in ("queen", "bishop", "tower"):
			ranges = []
			if curr in ("tower", "queen"):
				ranges.append(map(lambda q: (q, y), range(x, 8)))
				ranges.append(map(lambda q: (q, y), range(x, -1, -1)))
				ranges.append(map(lambda q: (x, q), range(y, 8)))
				ranges.append(map(lambda q: (x, q), range(y, -1, -1)))
			if curr in ("bishop", "queen"):
				ranges.append(map(lambda q: (x+q, y+q), range(min(8-x, 8-y))))
				ranges.append(map(lambda q: (x+q, y-q), range(min(8-x, y+1))))
				ranges.append(map(lambda q: (x-q, y+q), range(min(x+1, 8-y))))
				ranges.append(map(lambda q: (x-q, y-q), range(min(x+1, y+1))))
			
			for r in ranges:
				for check in r:
					if check == (x, y): continue
					
					dest = board[check[0]][check[1]]
					if not dest:
						out.append(check)
					elif dest:
						if dest[0] != color or offensive:#if enemy:
							out.append(check)
						break
		elif curr == "knight":
			for a, b in ((1, 2), (2, 1)):
				for check in ((x+a, y+b), (x-a, y+b), (x+a, y-b), (x-a, y-b)):
					if 0<=check[0]<8 and 0<=check[1]<8:
						dest = board[check[0]][check[1]]
						if (dest and dest[0] == color) and not offensive: continue
						out.append(check)
	
		#if doKingCheck and player.inCheck and not offensive:
		if doKingCheck and not offensive:
			for i in out[:]:
				nextPlayer = deepcopy(player)
				newboard = MakeMove(deepcopy(board), nextPlayer, (x, y), i)
				nextPlayer.WhitesTurn = player.WhitesTurn
				if isInCheck(newboard, nextPlayer):
					out.remove(i)
	
	return out#list of legal moves in coordinates

def isInCheck(board, player):
	enemy = "wb"[1*player.WhitesTurn]
	vulnerable = []
	king = None
	for x in range(8):
		for y in range(8):
			if board[x][y]:
				if board[x][y][0] == enemy:#for each enemy:
					vulnerable.extend(GetLegalMoves(board, player, (x, y), doKingCheck=False))
				elif board[x][y][0] != enemy and board[x][y][1:] == "king":
					king = (x, y)
	return king in vulnerable

def MakeMove(board, player, start, end):
	player.inCheck = False
	piece = board[start[0]][start[1]]
	
	#pawn reaching the end of the board:
	#if end[1] == 7*(piece[0]=="b") and piece[1:]=="pawn": piece = piece[0] + "queen"
	if end[1] == 7*(piece[0]=="b") and piece[1:]=="pawn": player.promotion = end
	
	board[start[0]][start[1]] = None
	board[end[0]][end[1]] = piece
	player.WhitesTurn = not player.WhitesTurn
	player.Selected = None
	
	player.inCheck = isInCheck(board, player)
	player.epoch = time.time()
	
	return board

class Graphics:
	def __init__(self):
		self.textures = {}
		self.sprites = {}
		for i in ("pawn", "king", "bishop", "knight", "tower", "queen", "back", "play", "mark", "prompt"):
			self.textures[i] = (sf.Texture.from_file("gfx/w%s.png" % i), sf.Texture.from_file("gfx/b%s.png" % i))
			self.sprites[i] = (sf.Sprite(self.textures[i][0]), sf.Sprite(self.textures[i][1]))
		for i in range(2): self.sprites["prompt"][i].position = sf.Vector2(256, 448)
	def DrawBoard(self, window, board, player):
		checkmate = True
		for x in range(8):
			for y in range(8):
				pos = sf.Vector2(x*128, y*128)
				#tile
				self.sprites["back"][(x+y)%2].position = pos
				window.draw(self.sprites["back"][(x+y%2)%2])
				
				#piece
				if board[x][y]:
					piece = board[x][y][1:]
					color = (board[x][y][0] == "b")*1
					self.sprites[piece][color].position = pos
					window.draw(self.sprites[piece][color])
					
					#playable piece:
					if (not color and player.WhitesTurn) or (color and not player.WhitesTurn):
						if GetLegalMoves(board, player, (x, y)):
							self.sprites["play"][0].position = pos
							window.draw(self.sprites["play"][0])
							checkmate = False
						
						if player.inCheck and piece == "king":
							self.sprites["mark"][1].position = pos
							window.draw(self.sprites["mark"][1])
		if checkmate:
			if (time.time()-player.epoch) % 2 < 1: window.draw(self.sprites["prompt"][0])
		elif player.promotion:
			mx, my = int(sf.Mouse.get_position(window).x*1024/window.size[0]), int(sf.Mouse.get_position(window).y*1024/window.size[1])
			window.draw(self.sprites["prompt"][1])
			for i, p in enumerate(("queen", "bishop", "tower", "knight")):
				self.sprites[p][player.WhitesTurn*1].position = sf.Vector2(256+128*i, 448)
				window.draw(self.sprites[p][player.WhitesTurn*1])
				if 256+128*i<=mx<384+128*i and 448<=my<576:
					self.sprites["play"][0].position = sf.Vector2(256+128*i, 448)
					window.draw(self.sprites["play"][0])
		elif player.Selected:
			self.sprites["play"][1].position = sf.Vector2(player.Selected[0]*128, player.Selected[1]*128)
			window.draw(self.sprites["play"][1])
			
			for i in GetLegalMoves(board, player):
				c = 1*bool(board[i[0]][i[1]])#wether a pice lies there or not
				self.sprites["mark"][c].position = sf.Vector2(i[0]*128, i[1]*128)
				window.draw(self.sprites["mark"][c])

def main():
	#init:
	window = sf.RenderWindow(sf.VideoMode(1024, 1024), "pbsds' chess")
	windowSize = (1024, 1024)
	gfx = Graphics()
	
	#make the board:
	board = MakeBoard()
	
	class player:
		WhitesTurn = True
		Selected = None#(x, y)
		inCheck = False
		promotion = None#coordinates of pawn in question
		epoch = None#used for eye-candy
	player = player()
	
	while window.is_open:
		#events:
		for event in window.events:
			e = type(event)
			if e is sf.CloseEvent:
				window.close()
			elif e is sf.MouseButtonEvent:
				if event.pressed:
					x, y = int(event.position.x*1024/window.size[0]), int(event.position.y*1024/window.size[1])
					if player.promotion:
						if 448<=y<576 and 256<=x<768:
							board[player.promotion[0]][player.promotion[1]] = board[player.promotion[0]][player.promotion[1]][0] + ("queen", "bishop", "tower", "knight")[(x-256)//128]
							player.promotion = None
							player.inCheck = isInCheck(board, player)
					else:
						x = x//128
						y = y//128
						if event.button == 0:#left click
							if board[x][y] and ((board[x][y][0]=="w" and player.WhitesTurn) or (board[x][y][0]=="b" and not player.WhitesTurn)):
								if GetLegalMoves(board, player, (x, y)):
									player.Selected = None if player.Selected == (x, y) else (x, y)
							elif (x, y) in GetLegalMoves(board, player):
								board = MakeMove(board, player, player.Selected, (x, y))
		
		#draw
		window.clear()
		gfx.DrawBoard(window, board, player)
		window.display()

main()