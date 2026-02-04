import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Icon } from "@/components/ui/icon"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Settings, Camera, Check, Alert } from "lucide-react"

export function ComponentTest() {
  return (
    <div className="p-8 space-y-8 bg-bg-primary text-text-primary">
      {/* Button Tests */}
      <Card>
        <CardHeader>
            <CardTitle>Button Components</CardTitle>
            <CardDescription>Test keyboard navigation and focus states</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="danger">Danger</Button>
          </div>
          <div className="flex gap-4">
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
          </div>
        </CardContent>
      </Card>

      {/* Input Tests */}
      <Card>
        <CardHeader>
            <CardTitle>Input Components</CardTitle>
            <CardDescription>Test validation states and keyboard navigation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="input-default">Default Input</Label>
            <Input id="input-default" placeholder="Enter text..." />
          </div>
          <div>
            <Label htmlFor="input-error" required>Error Input</Label>
            <Input id="input-error" state="error" placeholder="This has an error" />
          </div>
        </CardContent>
      </Card>

      {/* Badge Tests */}
      <Card>
        <CardHeader>
            <CardTitle>Badge Components</CardTitle>
            <CardDescription>Test semantic color variants</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Badge variant="default">Default</Badge>
          <Badge variant="primary">Primary</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="error">Error</Badge>
          <Badge variant="info">Info</Badge>
        </CardContent>
      </Card>

      {/* Icon Tests */}
      <Card>
        <CardHeader>
            <CardTitle>Icon Components</CardTitle>
            <CardDescription>Test consistent sizing</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Icon icon={Settings} size={16} className="text-primary-500" />
          <Icon icon={Camera} size={20} className="text-text-primary" />
          <Icon icon={Check} size={24} className="text-success-500" />
          <Icon icon={Alert} size={32} className="text-error-500" />
        </CardContent>
      </Card>

      {/* Dialog Tests */}
      <Card>
        <CardHeader>
            <CardTitle>Dialog Component</CardTitle>
            <CardDescription>Test focus trap and keyboard dismissal</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog>
            <DialogTrigger asChild>
              <Button>Open Dialog</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Test Dialog</DialogTitle>
                <DialogDescription>
                  This dialog should trap focus and close with Escape.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Label htmlFor="dialog-input">Input inside dialog</Label>
                <Input id="dialog-input" placeholder="Type to test focus trap..." />
                <div className="flex justify-end gap-2">
                  <Button variant="secondary">Cancel</Button>
                  <Button>Confirm</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  )
}
